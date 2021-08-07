from datetime import date
from odoo import fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    waybill_id = fields.Many2one(
        "stock.waybill", string="Накладная", compute="_get_waybill_id"
    )

    def _get_waybill_id(self):
        self.waybill_id = self.env["stock.waybill"].search(
            [("picking_id", "=", self.id)], limit=1
        )

    def action_create_waybill(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "name": _("Накладная"),
            "res_model": "stock.waybill",
        }
        context = {
            "default_agreement_id": self.sale_id.agreement_id.id,
            "default_sale_order_id": self.sale_id.id,
            "default_partner_id": self.sale_id.partner_id.id,
            "default_date_waybill": date.today(),
            "default_picking_id": self.id,
        }
        if self.sale_id.invoice_ids:
            for invoice in self.sale_id.invoice_ids:
                for line in invoice.invoice_line_ids:
                    if "Авансовый платеж" in line.name and line.quantity > 0:
                        context.update({"default_move_id": invoice.id})
        action["context"] = context
        return action
