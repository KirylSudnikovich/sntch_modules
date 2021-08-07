# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_round


class StockWayBill(models.Model):
    _name = "stock.waybill"
    _inherit = "mail.thread"
    _description = "Накладная"
    _order = "date_waybill desc"

    def _get_report_name(self):
        self.ensure_one()
        return "%s-%s-%s" % (self.series, self.number, self.date_waybill)

    def _get_byn_currency(self):
        return self.env["res.currency"].search([("name", "=", "BYN")])

    name = fields.Char(compute="_get_waybill_name", store=True)
    number = fields.Char(string="Номер", required=True)
    series = fields.Char(string="Серия", required=True)
    bill_type_id = fields.Selection(
        [("tn", "Товарная Накладная"), ("ttn", "Товарно-Транспортная Накладная")],
        string="Тип накладной",
        default="tn",
    )
    date_waybill = fields.Date(string="Дата накладной")
    agreement_id = fields.Many2one("agreement", string="Договор", required=True)
    sale_order_id = fields.Many2one("sale.order", string="Заказ", required=True)
    picking_id = fields.Many2one("stock.picking", string="Доставка", required=True)
    move_id = fields.Many2one("account.move", string="Аванс")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(),
    )
    company_id_vat = fields.Char(related="company_id.vat")
    company_id_info = fields.Char(compute="_get_company_id_info", string="Адрес")
    partner_id = fields.Many2one("res.partner", string="Контрагент", required=True)
    partner_id_vat = fields.Char(related="partner_id.vat")
    partner_id_info = fields.Char(compute="_get_partner_id_info", string="Адрес")
    state = fields.Selection(
        [
            ("draft", "Черновик"),
            ("done", "Проведен"),
            ("cancel", "Отменен"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default="draft",
    )
    supplement = fields.Boolean(string="Печать с приложением")
    order_line = fields.One2many(
        "stock.waybill.line", "waybill_id", string="Содержимое"
    )
    currency_id = fields.Many2one(
        "res.currency", string="Валюта", related="sale_order_id.currency_id"
    )
    currency_id_byn = fields.Many2one("res.currency", default=_get_byn_currency)
    amount_untaxed = fields.Float(
        string="Сумма отгрузки в валюте", compute="_compute_amount"
    )
    amount_tax = fields.Float(string="Сумма налога в валюте", compute="_compute_amount")
    amount_total = fields.Float(
        string="Итоговая сумма в валюте", compute="_compute_amount"
    )
    amount_down = fields.Float(string="Сумма аванса", compute="_compute_down_amount")
    amount_total_byn = fields.Float(
        string="Сумма накладной в брб", compute="_get_amount_total_byn"
    )
    weight_total = fields.Float(compute="_compute_weight_total", store=True)
    capacity_total = fields.Integer(compute="_compute_capacity_total", store=True)
    employee_id_1 = fields.Many2one("hr.employee", string="Отпуск разрешил")
    employee_id_2 = fields.Many2one("hr.employee", string="Сдал")
    client_employee = fields.Char(string="Товар к доставке принял")
    receipt = fields.Char(string="Довереность")
    receipt_author_id = fields.Char(string="Организация")
    waybill_get_employee = fields.Char(string="Принял грузополучатель")
    documents = fields.Char(string="Переданы документы")
    from_partner_id = fields.Many2one(
        "res.partner",
        string="Пункт погрузки",
        default=lambda self: self.env.company.partner_id,
    )
    to_partner_id = fields.Many2one("res.partner", string="Пункт разгрузки")
    payer = fields.Many2one(
        "res.partner", string="Заказчик автомобильной перевозки (плательщик)"
    )
    company_id_landing_type = fields.Selection(
        [("manual", "руч."), ("mech", "мех.")],
        string="Способ погрузки",
        default="manual",
    )
    partner_id_landing_type = fields.Selection(
        [("manual", "руч."), ("mech", "мех.")],
        string="Способ разгрузки",
        default="manual",
    )
    car = fields.Char(string="Автомобиль")
    trailer = fields.Char(string="Прицеп")
    drive_bill = fields.Char(string="Путевой лист")
    driver = fields.Char(string="Водитель")

    @api.depends("move_id", "amount_total")
    def _compute_down_amount(self):
        for waybill in self:
            if waybill.sale_order_id.amount_total:
                waybill.amount_down = float_round(
                    (waybill.move_id.amount_total - waybill.move_id.amount_residual)
                    / waybill.sale_order_id.amount_total
                    * waybill.amount_total,
                    2,
                )

    @api.depends("order_line.weight")
    def _compute_weight_total(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.weight
            order.weight_total = total

    @api.depends("order_line.capacity")
    def _compute_capacity_total(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.capacity
            order.capacity_total = total

    @api.depends("order_line.price_total")
    def _compute_amount(self):
        for waybill in self:
            amount_untaxed = amount_tax = 0.0
            for line in waybill.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            waybill.update(
                {
                    "amount_untaxed": float_round(amount_untaxed, 2),
                    "amount_tax": float_round(amount_tax, 2),
                    "amount_total": float_round(amount_untaxed + amount_tax, 2),
                }
            )

    def _get_amount_total_byn(self):
        for waybill in self:
            if waybill.currency_id.name == "BYN":
                waybill.amount_total_byn = float_round(waybill.amount_total, 2)
            elif waybill.currency_id.name == "USD":
                if waybill.move_id:
                    payments_ids = [
                        payment["account_payment_id"]
                        for payment in waybill.move_id._get_reconciled_info_JSON_values()
                    ]
                    payments = self.env["account.payment"].browse(payments_ids)
                    payments = set(payments)
                    down_amount_byn = 0
                    down_amount_byn_prep = 0
                    down_amount_usd = 0
                    for payment in payments:
                        payment_date = payment.date
                        rate_payment_date = self.env["res.currency.rate"].search(
                            [("name", "=", payment_date), ("currency_id", "=", "BYN")]
                        )
                        if payment.currency_id.name == "USD":
                            down_amount_usd += payment.amount
                            down_amount_byn_prep += (
                                payment.amount * rate_payment_date.rate
                            )
                            if down_amount_usd > waybill.amount_down:
                                diff = down_amount_usd - waybill.amount_down
                                down_amount_byn_prep -= diff * rate_payment_date.rate
                                down_amount_usd = waybill.amount_down
                            else:
                                down_amount_byn += (
                                    payment.amount * rate_payment_date.rate
                                )
                        else:
                            down_amount_usd += payment.amount / rate_payment_date.rate
                            down_amount_byn_prep += payment.amount
                            if down_amount_usd > waybill.amount_down:
                                diff = down_amount_usd - waybill.amount_down
                                down_amount_byn_prep -= diff * rate_payment_date.rate
                                down_amount_usd = waybill.amount_down
                    down_amount_byn = down_amount_byn_prep
                else:
                    down_amount_byn = 0
                rate_waybill_date = self.env["res.currency.rate"].search(
                    [("name", "=", waybill.date_waybill), ("currency_id", "=", "BYN")]
                )
                residual_amount_byn = (
                    waybill.amount_total - waybill.amount_down
                ) * rate_waybill_date.rate
                waybill.amount_total_byn = float_round(
                    down_amount_byn + residual_amount_byn, 2
                )
            elif waybill.currency_id.name == "EUR":
                if waybill.move_id:
                    byn_rate_payment_date = self.env["res.currency.rate"].search(
                        [("name", "=", payment_date), ("currency_id", "=", "BYN")]
                    )
                    eur_rate_payment_date = self.env["res.currency.rate"].search(
                        [("name", "=", payment_date), ("currency_id", "=", "EUR")]
                    )
                    payments_ids = [
                        payment["account_payment_id"]
                        for payment in waybill.move_id._get_reconciled_info_JSON_values()
                    ]
                    payments = self.env["account.payment"].browse(payments_ids)
                    payments = set(payments)
                    down_amount_byn = 0
                    down_amount_byn_prep = 0
                    down_amount_eur = 0
                    for payment in payments:
                        payment_date = payment.date
                        if payment.currency_id.name == "EUR":
                            down_amount_eur += payment.amount
                            down_amount_byn_prep += (
                                payment.amount
                                / eur_rate_payment_date
                                * byn_rate_payment_date.rate
                            )
                            if down_amount_eur > waybill.amount_down:
                                diff = down_amount_eur - waybill.amount_down
                                down_amount_byn_prep -= (
                                    diff
                                    / eur_rate_payment_date
                                    * byn_rate_payment_date.rate
                                )
                                down_amount_eur = waybill.amount_down
                            else:
                                down_amount_byn += (
                                    payment.amount
                                    / eur_rate_payment_date
                                    * byn_rate_payment_date.rate
                                )
                        else:
                            down_amount_eur += (
                                payment.amount
                                * eur_rate_payment_date.rate
                                / byn_rate_payment_date
                            )
                            down_amount_byn_prep += payment.amount
                            if down_amount_eur > waybill.amount_down:
                                diff = down_amount_eur - waybill.amount_down
                                down_amount_byn_prep -= (
                                    diff
                                    / eur_rate_payment_date.rate
                                    * byn_rate_payment_date.rate
                                )
                                down_amount_eur = waybill.amount_down
                    down_amount_byn = down_amount_byn_prep
                else:
                    down_amount_byn = 0
                byn_rate_payment_date = self.env["res.currency.rate"].search(
                    [("name", "=", waybill.date_waybill), ("currency_id", "=", "BYN")]
                )
                eur_rate_payment_date = self.env["res.currency.rate"].search(
                    [("name", "=", waybill.date_waybill), ("currency_id", "=", "EUR")]
                )
                residual_amount_byn = (
                    (waybill.amount_total - waybill.amount_down)
                    / eur_rate_payment_date.rate
                    * byn_rate_payment_date.rate
                )
                waybill.amount_total_byn = float_round(
                    down_amount_byn + residual_amount_byn, 2
                )
            elif waybill.currency_id.name == "RUB":
                if waybill.move_id:
                    payments = self.env["account.payment"].search(
                        [("ref", "=", waybill.move_id.name)]
                    )
                    byn_rate_payment_date = self.env["res.currency.rate"].search(
                        [
                            ("name", "=", payment_date),
                            ("currency_id", "=", "BYN"),
                        ]
                    )
                    rub_rate_payment_date = self.env["res.currency.rate"].search(
                        [
                            ("name", "=", payment_date),
                            ("currency_id", "=", "RUB"),
                        ]
                    )
                    down_amount_byn = 0
                    down_amount_byn_prep = 0
                    down_amount_rub = 0
                    for payment in payments:
                        payment_date = payment.date
                        rate_payment_date = self.env["res.currency.rate"].search(
                            [("name", "=", payment_date), ("currency_id", "=", "BYN")]
                        )
                        if payment.currency_id.name == "RUB":
                            down_amount_rub += payment.amount
                            down_amount_byn_prep += (
                                payment.amount
                                / rub_rate_payment_date
                                * byn_rate_payment_date.rate
                            )
                            if down_amount_eur > waybill.amount_down:
                                diff = down_amount_eur - waybill.amount_down
                                down_amount_byn_prep -= (
                                    diff
                                    / rub_rate_payment_date
                                    * byn_rate_payment_date.rate
                                )
                                down_amount_eur = waybill.amount_down
                            else:
                                down_amount_byn += (
                                    payment.amount
                                    / rub_rate_payment_date
                                    * byn_rate_payment_date.rate
                                )
                        else:
                            down_amount_byn += payment.amount
                            down_amount_rub += (
                                payment.amount
                                * rub_rate_payment_date.rate
                                / byn_rate_payment_date
                            )
                            down_amount_byn_prep += payment.amount
                            if down_amount_rub > waybill.amount_down:
                                diff = down_amount_rub - waybill.amount_down
                                down_amount_byn_prep -= (
                                    diff
                                    / rub_rate_payment_date.rate
                                    * byn_rate_payment_date.rate
                                )
                                down_amount_rub = waybill.amount_down
                    down_amount_byn = down_amount_byn_prep
                else:
                    down_amount_byn = 0
                residual_amount_byn = (
                    (waybill.amount_total - waybill.amount_down)
                    / rub_rate_payment_date.rate
                    * byn_rate_payment_date.rate
                )
                waybill.amount_total_byn = float_round(
                    down_amount_byn + residual_amount_byn, 2
                )

    @api.model_create_multi
    def create(self, vals):
        res = super(StockWayBill, self).create(vals)
        if res.sale_order_id and res.picking_id:
            for line in res.picking_id.move_line_ids_without_package:
                for sale_line in res.sale_order_id.order_line:
                    if line.product_id == sale_line.product_id:
                        waybill_line = self.env["stock.waybill.line"].create(
                            {
                                "product_id": line.product_id.id,
                                "product_uom": line.product_uom_id.id,
                                "lot_id": line.lot_id.id,
                                "product_uom_qty": line.qty_done,
                                "price_unit": sale_line.price_unit_discounted,
                                "waybill_id": res.id,
                            }
                        )
                        waybill_line._onchange_weight()
                        waybill_line._onchange_capacity()
                        waybill_line.tax_id = sale_line.tax_id
        return res

    def _get_company_id_info(self):
        company_name = self.with_context(lang=self.partner_id.lang).company_id.name
        address = f"{self.company_id.city}, {self.company_id.street}"
        self.company_id_info = f"{company_name}, {address}"

    def _get_partner_id_info(self):
        partner_name = self.with_context(lang=self.partner_id.lang).partner_id.name
        address = f"{self.partner_id.city}, {self.partner_id.street}"
        self.partner_id_info = f"{partner_name}, {address}"

    @api.depends("series", "number")
    def _get_waybill_name(self):
        if self.series and self.number:
            self.name = f"{self.series} {self.number}"
        elif self.series and not self.number:
            self.name = f"{self.series}"
        elif self.number and not self.series:
            self.name = f"{self.number}"

    def action_confirm(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_draft(self):
        self.write({"state": "draft"})
