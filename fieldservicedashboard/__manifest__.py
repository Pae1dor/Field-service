{
    'name': 'Field Service Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Operations/Field Service',
    'summary': 'Dashboard to monitor technician schedule, calendar, and On Process status',
    'depends': ['fieldservice'],
    'data': [
        'security/ir.model.access.csv',
        'views/calendar_views.xml',
        'views/dashboard_menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}