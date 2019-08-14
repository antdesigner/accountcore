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
        'report/account_subsidiary_book_template.xml',
        'views/menu.xml',
        'data/default_data.xml',
        'data/help_data.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'views/btn_templates.xml',
        'static/xml/base_extend.xml',
    ],
    'demo': [
        'demo/users.xml',
        'demo/org.xml',
        'demo/items_wang_lai.xml',
        'demo/items_bu_men.xml',
        'demo/items_yuan_gong.xml',
        'demo/items_yuan_cai_liao.xml',
        'demo/items_ku_cun_shang_pin.xml',
        'demo/items_yuan_cai_liao.xml',
        'demo/items_yuan_cai_liao.xml',
        'demo/items_cheng_ben_fei_yong.xml',
        'demo/items_di_zhi_yi_hao.xml',
        'demo/items_gu_ding_zi_chan.xml',
        'demo/items_wu_xing_zi_chan.xml',
        'demo/accounts.xml',
    ],
    'css': [
        'static/css/accountcore.css',
    ],
    'post_init_hook': '_load_demo',
}
