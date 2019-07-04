# -*- coding: utf-8 -*-
import time
import copy
import decimal
from odoo import http
from odoo import exceptions
import json
from odoo import models, fields, api
import sys
sys.path.append('.\\.\\server')


class AccountBalanceReport(models.AbstractModel):
    _name = 'report.accountcore.account_balance_report'
    @api.model
    def _get_report_values(self, docids, data=None):
        form = data['form']
        account_ids = form['account']
        org_id = form['org']
        start_year = form['startDate'].year
        start_month = form['startMonth'].month
        end_year = form['endDate'].year
        end_month = form['endDate'].month
        all= self.env['accountcore.accounts_balance'].sudo().search(
            [('org', '=', org_id), ('account', 'in', account_ids)]).sorted(lambda a: (a.account, a.items, a.year, a.month))
        cr=self.env.cr
        # 查询期间又发生额的
        # query=''
        # cr.execute(query,params)
        return {'doc_ids': docids, 'doc_model': all, 'data': data}


class Balance(object):
    def __init__(self, account_id):
        self.account_id = account_id
        self.item_id = 0
        self.begin_damount = 0
        self.begin_damount = 0
        self.damount = 0
        self.camount = 0


class Balances(object):
    def __init__(self):
        pass
        self.accounts = {}
        self.accounts_item = {}

    def add(self, balance):
        '''添加一行余额记录'''
        self.accounts.update({balance.account_id: balance})
        mark = '-'.join(str(balance.accoun_id), str(balance.items))
        self.accounts_item.update({mark: balance})

    def exit(self, balance):
        '''存在相同科目和和核算项目的余额'''
        if balance.accounts_item in self.accounts_item:
            return True
        return False

    def exitAccount(self, balance):
        '''存在相同科目的余额'''
        if balance.accoun_id in self.accounts:
            return True
        return False

    def sorted(self):
        self.accounts = sorted(self.accounts.items, key=lambda x: x[0])
        self.accounts_item = sorted(
            self.accounts_item.items, key=lambda x: x[0])
