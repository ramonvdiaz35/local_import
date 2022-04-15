# -*- coding: utf-8 -*-
{
    'name': "local_import",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','freight'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/res_partner_views.xml',
        'views/freight_import_regimen.xml',
        'views/freight_aforo_type_views.xml',
        'views/freight_lote_views.xml',
        'views/compra_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/stock_landed_cost_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
