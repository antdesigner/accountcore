# -*- coding: utf-8 -*-
{
    'name': "AccountCore",

    'summary': """
       一个独立的会计模块""",

    'description': """
        Long description of module's purpose
    """,

    'author': "huangTiger",
    'website': "http://www.88v88v.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/default_data.xml'
    ],
    'qweb': [
        'views/accountcore.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'css': [
        'static/css/accountcore.css',
    ]
}
