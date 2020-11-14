# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.phone_validation.tools import phone_validation


class ResPartner(models.Model):
    _inherit = 'res.partner'

    duplicate_have = fields.Boolean(default=False)
    duplicate_ids = fields.Many2many('res.partner', compute='_find_contact_duplicates')
    duplicate_len = fields.Integer(compute='_find_contact_duplicates')

    @api.model
    def create(self, vals):
        if not self._get_duplicate_check():
            res = super(ResPartner, self).create(vals)
        else:
            res = super(ResPartner, self).create(vals)
            fields_to_check = self._get_duplicate_check_fields()
            if fields_to_check:
                duplicates = self.find_duplicate_by_fields(vals, fields_to_check)
                if duplicates and not self.check_user_in_whitelist():
                    dups_to_err = self.create_dups_error_message(fields_to_check, duplicates, vals)
                    str_to_err = self._create_error_str(dups_to_err)
                    raise UserError(_(str_to_err))
                if duplicates and self.check_user_in_whitelist():
                    for duplicate_field in duplicates:
                        for duplicate in duplicate_field:
                            if not duplicate.duplicate_have:
                                duplicate.duplicate_have = True
                    res.duplicate_have = True
        return res

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if self._get_duplicate_check():
            fields_to_check = self._get_duplicate_check_fields()
            if fields_to_check:
                duplicates = self.find_duplicate_by_object(fields_to_check)
                if duplicates and not self.check_user_in_whitelist():
                    dups_to_err = self.create_dups_error_message(fields_to_check, duplicates)
                    str_to_err = self._create_error_str(dups_to_err)
                    raise UserError(_(str_to_err))
                if duplicates and self.check_user_in_whitelist():
                    for duplicate_field in duplicates:
                        for duplicate in duplicate_field:
                            if not duplicate.duplicate_have:
                                duplicate.duplicate_have = True
                    if not self.duplicate_have:
                        self.duplicate_have = True
        return res

    def action_get_duplicates_tree_view(self):
        action = self.env.ref('contacts.action_contacts').read()[0]
        action['domain'] = [('id', 'in', self.duplicate_ids.ids)]
        action['context'] = dict(self._context)
        return action

    def _get_contact_duplicates_domain(self, f):
        domain = [(f.field, '=', getattr(self, f.field)),
            ('id', '!=', self.id), (f.field, '!=', False)]
        return domain

    def _find_contact_duplicates(self):
        fields_to_check = self._get_duplicate_check_fields()
        res_partner_env = self.env['res.partner']
        dups = res_partner_env.browse([])
        for f in fields_to_check:
            domain = self._get_contact_duplicates_domain(f)
            dup = res_partner_env.search(domain)
            dups += dup
        if dups:
            self.duplicate_ids = dups
            self.duplicate_len = len(dups)
            if not self.duplicate_have:
                self.duplicate_have = True
        else:
            if self.duplicate_have:
                self.duplicate_have = False
            self.duplicate_len = 0

    def _get_duplicate_by_fields_domain(self, vals_list, f):
        domain = [(f.field, '=', vals_list.get(f.field)),
            (f.field, '!=', False)]
        return domain

    def plivo_phone_format(self, number=None, country=None, company=None):
        country = country or self._phone_get_country()
        if not country:
            return number
        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format='E164',
            raise_exception=False
        )

    def find_dups_by_phone(self, vals_list, f):
        dups = self.env['res.partner'].browse()
        contacts = self.env['res.partner'].search([])
        for contact in contacts:
            phone = self.plivo_phone_format(contact.phone)[-9:] if contact.phone else False
            mobile = self.plivo_phone_format(contact.mobile)[-9:] if contact.mobile else False
            vals_phone = self.plivo_phone_format(vals_list.get(f.field))[-9:] if vals_list.get(f.field) else False
            if vals_phone and (vals_phone == phone or vals_phone == mobile):
                dups += contact
        return dups

    def find_duplicate_by_fields(self, vals_list, fields_to_check):
        result = []
        self.env.context = dict(self.env.context)
        self.env.context['dup_fields'] = []
        res_partner_env = self.env['res.partner']
        for f in fields_to_check:
            if f.field != 'phone' and f.field != 'mobile':
                domain = self._get_duplicate_by_fields_domain(vals_list, f)
                dups = res_partner_env.search(domain)
            else:
                dups = self.find_dups_by_phone(vals_list, f)
            if dups:
                self.env.context['dup_fields'].append(f.field)
                result.append(dups)
        return result

    def _get_duplicate_by_object_domain(self, f):
        domain = [(f.field, '=', getattr(self, f.field)),
            ('id', '!=', self.id), (f.field, '!=', False)]
        return domain

    def find_dups_by_phone_object(self, f):
        dups = self.env['res.partner'].browse()
        contacts = self.env['res.partner'].search([])
        for contact in contacts:
            if contact.id != self.id:
                phone = self.plivo_phone_format(contact.phone)[-9:] if contact.phone else False
                mobile = self.plivo_phone_format(contact.mobile)[-9:] if contact.mobile else False
                vals_phone = self.plivo_phone_format(getattr(self, f.field))[-9:] if getattr(self, f.field) else False
                if vals_phone and (vals_phone == phone or vals_phone == mobile):
                    dups += contact
        return dups

    def find_duplicate_by_object(self, fields_to_check):
        result = []
        self.env.context = dict(self.env.context)
        self.env.context['dup_fields'] = []
        res_partner_env = self.env['res.partner']
        for f in fields_to_check:
            if f.field != 'phone' and f.field != 'mobile':
                domain = self._get_duplicate_by_object_domain(f)
                dups = res_partner_env.search(domain)
            else:
                dups = self.find_dups_by_phone_object(f)
            if dups:
                self.env.context['dup_fields'].append(f.field)
                result.append(dups)
        return result

    def create_dups_error_message(self, fields_to_check, dups, vals_list=None):
        dups_to_str = []
        dup_fields = self.env.context.get('dup_fields', [])
        for index in range(len(dups)):
            dups_to_str.append([dup_fields[index], dups[index].mapped('name'),
                                dups[index].mapped('id')]) 
        return dups_to_str
    
    def check_user_in_whitelist(self):
        users = self._get_duplicate_whitelist()
        if not self.env.user in users:
            return False
        return True

    
    def _create_entity_link(self, partner_name, partner_id):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        base_url = get_param('web.base.url').rstrip('/')
        link =  f'<a href="{base_url}/web#id={partner_id}&amp;"\
                "model=res.partner&amp;view_type=form">{partner_name or partner_id}</a>'
        return link

    @api.model
    def _create_error_str(self, duplicates):
        result_str = ""
        for field in duplicates:
            result_str += "Duplicates were found for the field '{}':\n".format(field[0])
            for index in range(len(field[1])):
                result_str += "{}) {} (ID={});\n".format(index+1, field[1][index], field[2][index])
        return result_str
        
    @api.model
    def _get_duplicate_check(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        return get_param('contact_deduplicate.duplicate_check')

    @api.model
    def _get_duplicate_check_fields(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        f_ids = get_param('contact_deduplicate.duplicate_check_fields')
        f_ids = eval(f_ids) if f_ids else []
        fields = self.env['res.partner.fields'].browse(f_ids)
        return fields
    
    @api.model
    def _get_duplicate_whitelist(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        u_ids = get_param('contact_deduplicate.user_whitelist')
        u_ids = eval(u_ids) if u_ids else []
        users = self.env['res.users'].browse(u_ids)
        return users