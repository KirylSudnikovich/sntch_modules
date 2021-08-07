# -*- coding: utf-8 -*-
{
    "name": "Склад: Накладные",
    "summary": """Модуль печатных ТН/ТТН форм для Республики Беларусь""",
    "author": "Malanka OU",
    "website": "https://malanka.eu",
    "category": "Inventory",
    "version": "14.0.0.3.8",
    "price": "299.99",
    "currency": "EUR",
    "license": "OPL-1",
    "depends": [
        "sale_stock",
        "hr",
        # OCA-repository https://github.com/OCA/contract/tree/14.0/agreement
        # "agreement",
        # OCA-repository https://github.com/OCA/reporting-engine/tree/14.0
        # "report_xlsx",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_views.xml",
        "views/waybill_views.xml",
    ],
}
