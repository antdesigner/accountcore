# -*- coding: utf-8 -*-
{
    'name': "AccountCore(会计)",
    'summary': """
       一个独立的中国会计模块""",
    'description': """
        会计总账和报表功能，和odoo自带的会计模块完全无关。以简单、直接、易用、智能为设计原则。没有繁琐的初始化和配置，不用结账和反结账、过账等冗余操作是中国会计的最佳实践。
    """,
    'author': "黄虎",
    'website': "",
    'category': 'accountcore',
    'version': '12.1.3.20200411_beta',
    'price': 333.85,
    'currency': 'USD',
    'depends': ['base', 'web'],
    'application': True,
    'license': 'LGPL-3',
    'images': [
        'static/images/main_screenshot.png',
        'static/description/icon.png',
        'static/description/accountbalance.png',
        'static/description/begining.png',
        'static/description/cashflow.png',
        'static/description/report.png',
        'static/description/searchentry.png',
        'static/description/subsidiarybook.png',
        'static/description/voucher.png', ],
    'data': [
        'views/assetsAdd_templates.xml',
        'security/users.xml',
        'views/views.xml',
        'report/voucher_print_templates.xml',
        'report/account_balance_report_template.xml',
        'report/account_subsidiary_book_template.xml',
        'views/reports.xml',
        'views/autoNumber.xml',
        'views/menu.xml',
        'data/default_data.xml',
        'data/report_model.xml',
        'data/help_data.xml',
        'security/ir.model.access.csv',
        'security/record_group_role_ac.xml',
        'security/record_group_role_search.xml',
        'security/record_group_system.xml',

    ],
    'qweb': [
        'views/btn_templates.xml',
        'static/xml/jexcel.xml',
        'static/xml/base_extend.xml',
    ],
    'css': [
        'static/css/accountcore.css',
        'static/css/jexcel.css',
        'static/css/jsuites.css',
    ],
}
