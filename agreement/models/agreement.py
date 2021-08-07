from odoo import _, api, models, fields


class Agreement(models.Model):
    _name = "agreement"
    _description = "Agreement"
    _inherit = ["mail.thread"]

    code = fields.Char(compute="_get_agreement_code", store=True)
    name = fields.Char(required=True, track_visibility="onchange")
    number = fields.Char(required=True, track_visibility="onchange")
    account_number = fields.Char(
        track_visibility="onchange", string="Идентификатор у клиента"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        ondelete="restrict",
        domain=[("parent_id", "=", False)],
        track_visibility="onchange",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    domain = fields.Selection(
        "_domain_selection",
        string="Domain",
        default="sale",
        track_visibility="onchange",
    )
    currency_id = fields.Many2one("res.currency", required=True)
    active = fields.Boolean(default=True)
    signature_date = fields.Date(track_visibility="onchange")
    start_date = fields.Date(track_visibility="onchange", required=True)
    end_date = fields.Date(track_visibility="onchange")
    signed_by = fields.Char(string="Подписант")

    @api.depends("currency_id", "number")
    def _get_agreement_code(self):
        for agr in self:
            if agr.currency_id and agr.number:
                agr.code = f"{agr.currency_id.name} {agr.number}"

    @api.model
    def _domain_selection(self):
        return [
            ("sale", _("Sale")),
            ("purchase", _("Purchase")),
        ]

    def name_get(self):
        res = []
        for agr in self:
            name = agr.name
            if agr.code:
                name = "[%s] %s" % (agr.code, agr.name)
            res.append((agr.id, name))
        return res

    _sql_constraints = [
        (
            "code_partner_company_unique",
            "unique(code, partner_id, company_id)",
            "This agreement code already exists for this partner!",
        )
    ]

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """Always assign a value for code because is required"""
        default = dict(default or {})
        if default.get("code", False):
            return super().copy(default)
        default.setdefault("code", _("%s (copy)") % (self.code))
        return super().copy(default)