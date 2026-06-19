{
    'name': 'Field Service - Sale Flow',
    'version': '17.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Quotation → FSM Order → Parts (Stock/PR) → Invoice',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['fieldservice', 'sale_management', 'stock', 'purchase_request'],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_order_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
