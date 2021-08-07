from odoo import api, models, fields
from odoo.tools import float_round


class StockWaybillLine(models.Model):
    _name = "stock.waybill.line"

    name = fields.Char(
        string="Наименование товара",
        compute="_get_waybill_line_name",
        inverse="_set_waybill_line_name",
    )
    waybill_id = fields.Many2one(
        "stock.waybill",
        string="Накладная",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True,
        ondelete="restrict",
        check_company=True,
    )  # Unrequired company
    product_uom = fields.Many2one("uom.uom", string="Единица измерения")
    product_uom_qty = fields.Float(
        string="Quantity", digits="Количество", required=True, default=1.0
    )
    price_unit = fields.Float(
        "Цена в валюте.", required=True, digits="Product Price", default=0.0
    )
    price_unit_byn = fields.Float(
        "Цена, руб. коп.",
        digits="Product Price",
        default=0.0,
        compute="_compute_price_unit_byn",
        inverse="_inverse_price_unit_byn",
    )
    price_subtotal = fields.Float(
        string="Стоимость в валюте", compute="_compute_amount", store=True
    )
    price_tax = fields.Float(
        string="Сумма НДС в валюте", compute="_compute_amount", store=True
    )
    price_total = fields.Float(
        string="Стоимость с НДС в валюте", compute="_compute_amount", store=True
    )
    price_subtotal_byn = fields.Float(
        string="Стоимость, руб. коп", compute="_compute_amount_byn", store=True
    )
    price_tax_byn = fields.Float(
        string="Сумма НДС, руб. коп", compute="_compute_amount_byn", store=True
    )
    price_total_byn = fields.Float(
        string="Стоимость с НДС, руб. коп", compute="_compute_amount_byn", store=True
    )
    tax_id = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    weight = fields.Float()
    capacity = fields.Integer()
    note = fields.Char(string="Примечание")
    lot_id = fields.Many2one(
        "stock.production.lot",
        "Lot/Serial Number",
        domain="[('product_id', '=', product_id)]",
        check_company=True,
    )

    @api.depends("product_id.weight_brutto")
    def _depends_weight(self):
        for line in self:
            line.weight = line.product_id.weight_brutto * line.product_uom_qty

    @api.onchange("product_uom_qty", "product_id")
    def _onchange_weight(self):
        for line in self:
            line.weight = line.product_id.weight_brutto * line.product_uom_qty

    @api.onchange("product_uom_qty", "product_uom")
    def _onchange_capacity(self):
        for line in self:
            if line.product_uom.id == 1:
                line.capacity = line.product_uom_qty
            elif line.product_uom.id == 8:
                line.capacity = float_round(
                    line.product_uom_qty / 305, 0, rounding_method="UP"
                )
            else:
                line.capacity = 0

    @api.depends("price_unit", "waybill_id.amount_total", "waybill_id.amount_total_byn")
    def _compute_price_unit_byn(self):
        for line in self:
            line.price_unit_byn = float_round(
                line.price_unit
                / line.waybill_id.amount_total
                * line.waybill_id.amount_total_byn,
                2,
            )
            line._compute_amount_byn()

    def _inverse_price_unit_byn(self):
        for line in self:
            line.price_unit_byn = 0

    @api.depends("price_unit_byn", "product_uom_qty")
    def _compute_amount_byn(self):
        for line in self:
            price = line.price_unit_byn
            taxes = line.tax_id.compute_all(
                price,
                line.waybill_id.sale_order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.waybill_id.partner_id,
            )
            line.update(
                {
                    "price_tax_byn": float_round(
                        sum(t.get("amount", 0.0) for t in taxes.get("taxes", [])), 2
                    )
                    if len(line.waybill_id.order_line) > 1
                    else float_round(
                        float_round(line.waybill_id.amount_total_byn, 2)
                        - float_round(line.waybill_id.amount_total_byn, 2) / 1.2,
                        2,
                    ),
                    "price_total_byn": float_round(taxes["total_included"], 2)
                    if len(line.waybill_id.order_line) > 1
                    else line.waybill_id.amount_total_byn,
                    "price_subtotal_byn": float_round(taxes["total_excluded"], 2),
                }
            )

    @api.depends("price_unit", "product_uom_qty")
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(
                price,
                line.waybill_id.sale_order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.waybill_id.partner_id,
            )
            line.update(
                {
                    "price_tax": float_round(
                        sum(t.get("amount", 0.0) for t in taxes.get("taxes", [])), 2
                    ),
                    "price_total": float_round(taxes["total_included"], 2),
                    "price_subtotal": float_round(taxes["total_excluded"], 2),
                }
            )

    @api.depends("product_id")
    def _get_waybill_line_name(self):
        for line in self:
            product = line.product_id
            line.name = f"{product.default_code}, {product.brand_id.name} {product.model if product.model != product.default_code else ''} {product.desc} "
            if line.lot_id:
                if line.lot_id.country_id:
                    line.name += f"/{line.lot_id.country_id.name}/"
                else:
                    line.name += f"/{line.product_id.country_id.name}/"
            else:
                line.name += f"/{line.product_id.country_id.name}/"

    def _set_waybill_line_name(self):
        for line in self:
            line.name = ""