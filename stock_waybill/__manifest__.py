# -*- coding: utf-8 -*-
{
    "name": "Склад: Накладные",
    "summary": """Модуль печатных ТН/ТТН форм для Республики Беларусь""",
    "author": "Malanka OU",
    "website": "https://malanka.eu",
    "category": "Inventory",
    "version": "14.0.0.3.8",
    "depends": [
        "sale_stock",
        "hr",
        "agreement",
        # OCA-repository https://github.com/OCA/reporting-engine/tree/14.0
        "report_xlsx",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_views.xml",
        "views/waybill_views.xml",
    ],
}
