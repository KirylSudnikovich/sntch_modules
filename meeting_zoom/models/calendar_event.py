from odoo import models, fields, api


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    is_zoom = fields.Boolean(string="Zoom need")

    def create(self, vals):
        res = super(CalendarEvent, self).create(vals)
        if res.is_zoom:
            print("Create meeting in Zoom")
            self.env['zoom.adapter'].create_meeting(res)
        return res