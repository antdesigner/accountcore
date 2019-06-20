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
    'depends': ['base'],
    'application': True,
    'images': ['static/description/icon.png'],
    'data': [
        'security/users.xml',
        'views/views.xml',
        'views/voucher_print.xml',
        'report/account_balance_report_temple.xml',
        'data/default_data.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'views/btn.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'css': [
        'static/css/accountcore.css',
    ]
}
