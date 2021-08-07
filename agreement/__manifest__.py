# -*- coding: utf-8 -*-
{
    "name": "Договоры",
    "summary": """Модуль для договоров внутри системы Odoo""",
    "author": "Kiryl Sudnikovich, Malanka OU",
    "website": "https://malanka.eu",
    "category": "Sales",
    "version": "14.0.0.0.1",
    "depends": [
        "base",
        "mail",
    ],
    "data": ["security/ir.model.access.csv", "views/agreement.xml"],
}
