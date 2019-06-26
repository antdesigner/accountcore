# -*- coding: utf-8 -*-
{
    'name': "AccountCore",
    'summary': """
       一个独立的中国会计模块""",
    'description': """
        和odoo自带的会计模块完全无关。以简单、直接、易用、智能为设计原则。没有繁琐的初始化和配置，不用结账和反结账、过账等冗余操作是中国会计的最佳实践。
    """,
    'author': "黄虎",
    'website': "http://www.baidu.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','web'],
    'application': True,
    'images': ['static/description/icon.png'],
    'data': [
        'views/assetsAdd_templates.xml',
        'security/users.xml',
        'views/views.xml',
        'report/voucher_print_templates.xml',
        'report/account_balance_report_template.xml',
        'views/menu.xml',
        'data/default_data.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'views/btn_templates.xml',
        'static/xml/base_extend.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'css': [
        'static/css/accountcore.css',
    ]
}
