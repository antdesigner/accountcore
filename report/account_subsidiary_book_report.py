# -*- coding: utf-8 -*-
# editor:huang tiger ###### Sun Jul 14 17:16:10 CST 2019
import time
import copy
import decimal
from odoo import http
from odoo import exceptions
import json
from odoo import models, fields, api
import datetime
import sys
sys.path.append('.\\.\\server')


class SubsidiaryBook(models.AbstractModel):
    '''科目余额表'''
    _name = 'report.accountcore.subsidiary_book_report'
    @api.model
    def _get_report_values(self, docids, data=None):
        form = data['form']
        # todo-tiger:'获取表单输入'
        startDate = datetime.datetime.strptime(form['startDate'], '%Y-%m-%d')
        endDate = datetime.datetime.strptime(form['endDate'], '%Y-%m-%d')
        org_ids = form['orgs']
        account_id = form['account']
        item_id = form['item']
        voucher_number_tastics_id = form['voucher_number_tastics']
        # todo-tiger:'构建报表数据'
        # todo-tiger:'查询数据库'
        entryArchs = self._getEntryArchData(params)
        # todo-tiger:'整理数'
        pass
        pass
        pass

        entrys = None
        return {'doc_ids': docids, 'docs': entrys, 'data': data}

    def _getData(self, params):
        query = """

        """
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()


class EntryArch(object):
    '''明细账明细'''

    def __init__(self, voucher_id, org_id, account_id, item_id):
        self.voucher_id = voucher_id
        self.voucherdate = None
        self.number = ""
        self.uniqueNumber = ""
        self.org_name = ''
        self.explain = ''
        self.account_numeber = ''
        self.account_name = ''
        self.items_name = ''
        self.damount = ''
        self.camount = ''
        self.direction = ""
        self.cashFlow = ''
