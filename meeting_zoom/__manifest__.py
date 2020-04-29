# -*- coding: utf-8 -*-
{
    'name': "Meetings: Zoom",
    'summary': """Meetings: Zoom module""",
    'description': """Meetings: Zoom module""",
    'author': 'Kirill Sudnikovich',
    'maintainer': 'Kirill Sudnikovich',
    'website': "https://sntch.dev",
    'category': 'CRM',
    'version': '13.0.0.0.0',
    'depends': ['base', 'calendar'],
    'data': [
        'views/res_company_views.xml',
        'views/calendar_event_views.xml'
    ],
    # 'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
