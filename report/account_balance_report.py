# -*- coding: utf-8 -*-
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


class AccountBalanceReport(models.AbstractModel):
    _name = 'report.accountcore.account_balance_report'
    @api.model
    def _get_report_values(self, docids, data=None):

        form = data['form']

        account_ids = form['account']
        org_id = form['org']
        startDate = datetime.datetime.strptime(form['startDate'], '%Y-%m-%d')
        start_year = startDate.year
        start_month = startDate.month
        endDate = datetime.datetime.strptime(form['endDate'], '%Y-%m-%d')
        end_year = endDate.year
        end_month = endDate.month

        params = (start_year, start_month, end_year,
                  end_month, tuple(org_id), tuple(account_ids))
        # 科目在查询期间的余额记录
        DandCAmounts = self._getDAndCAmount(params)
        params_befor_start = (start_year, start_year,
                              start_month, tuple(org_id))
        # 科目在查询期间以前的余额记录
        recordsBeforSart = self._getRecordsBeforStart(params_befor_start)
        balances = Balances()
        temp_accountId = ""
        temp_itemId = ""
        temp_orgId = ""
        for record in recordsBeforSart:
            # if 已经对开始期间以前的最近一条相同科目和核算项目的记录取了数，就跳到下一个record
            if record['org_id'] == temp_orgId and record['account_id'] == temp_accountId and record['item_id'] == temp_itemId:
                continue
            temp_orgId = record['org_id']
            temp_accountId = record['account_id']
            temp_itemId = record['item_id']
            # if 余额明细容器中已经存在，就跳到下一个record
            if balances.exit(temp_orgId, temp_accountId, temp_itemId):
                continue
            balance = Balance(temp_orgId, temp_accountId, temp_itemId)
            # 添加期初借贷方余额
            balance.account_class_id = record['account_class_id']
            balance.account_father_id = record['account_father_id']
            balance.account_id = record['account_id']
            balance.account_number = record['account_number']
            balance.account_name = record['account_name']
            balance.direction = record['direction']
            balance.item_class_id = record['item_class_id']
            balance.item_class_name = record['item_class_name']
            balance.item_number = record['item_number']
            balance.item_name = record['item_name']
            balance.beginingDamount = record['beginingDamount']
            balance.beginingCamount = record['beginingCamount']
            # if 在查询期间范围内有该科目和核算项目的借贷方发生额记录（若范围内没有发生额，则不会生成记录）
            balance_DAndCAmount = None
            for one in DandCAmounts:
                if one['org_id'] == balance.org_id and one['account_id'] == balance.account_id and one['item_id'] == balance.item_id:
                    balance_DAndCAmount = one
                    break
            if balance_DAndCAmount:
                # 添加查询期间的借贷方发生额
                balance.damount = balance_DAndCAmount['damount']
                balance.camount = balance_DAndCAmount['camount']
                balances.add(balance)
                balance_DAndCAmount['havepre'] = True
                continue
        # 添加查询期间有发生额，但查询期间之前没有余额记录的相关科目记录
        for one in DandCAmounts:
            if one['havepre'] == False:
                balance_current = Balance(temp_orgId,temp_accountId, temp_itemId)
                balance_current.org_id = one['org_id']
                balance_current.account_class_id = one['account_class_id']
                balance_current.account_father_id = one['account_father_id']
                balance_current.account_id = one['account_id']
                balance_current.account_number = one['account_number']
                balance_current.account_name = one['account_name']
                balance_current.direction = one['direction']
                balance_current.item_class_id = one['item_class_id']
                balance_current.item_class_name = one['item_class_name']
                balance_current.item_number = one['item_number']
                balance_current.item_name = one['item_name']
                balance_current.beginingDamount = 0
                balance_current.beginingCamount = 0
                balance.damount = one['damount']
                balance.camount = one['camount']
                balances.add(balance_current)

        return {'doc_ids': docids, 'docs': balances.org_account_items.values(), 'data': data}

    def _getRecordsBeforStart(self, params):
        '''获得查询日期前的余额记录,已经按科目项目年份月份进行排序，方便取查询期间范围前的最近一期的余额记录'''
        query = '''SELECT org_id,t2."accountClass" as account_class_id,
        t2."fatherAccountId" as account_father_id,
        t2.id as account_id,
        t2.number as account_number,
        t2.name as account_name,
        t2.direction ,
        t5.item_class_id,
        t5.item_class_name,
        t.item_id ,
        t5.item_number,
        t5.item_name,
        t."beginingDamount" ,
        t."beginingCamount" 
        FROM
                (SELECT
                    org as org_id,
                    account as account_id,
                    items as item_id ,
                    "beginingDamount",
                    "beginingCamount"       
                FROM
                    accountcore_accounts_balance
                WHERE   
                    (year > %s
                    OR
                    year =%s AND month <= %s)
                    AND
                    org in %s
                ORDER BY
                    org,account,items,year desc ,month desc,isbegining desc)
        AS t
        LEFT OUTER JOIN  accountcore_account as t2 
        ON t.account_id =t2.id
        LEFT OUTER JOIN (select t4.id as item_class_id,
                            t4.name as item_class_name, 
                            t3.id as item_id,
                            t3.number as item_number,
                            t3.name as item_name
                        from  accountcore_item as t3 
                        left outer join accountcore_itemclass as t4 
                        on  t3."itemClass"=t4.id) 
                        as t5
        ON t.item_id=t5.item_id'''
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _getDAndCAmount(self, params):
        '''在查找期间的发生额'''
        # 当期借贷方发生额合计
        query = '''SELECT org_id, t2."accountClass" as account_class_id,
        t2."fatherAccountId" as account_father_id,
        t2.id as account_id,
        t2.number as account_number,
        t2.name as account_name,
        t2.direction ,
        t5.item_class_id,
        t5.item_class_name,
        t.item_id ,
        t5.item_number,
        t5.item_name,
        t.damount ,
        t.camount ,
        False as havepre 
        FROM
                (SELECT  org as org_id,
                        account as account_id,
                        items as item_id ,
                        sum(damount) as damount,
                        sum(camount)as camount
                FROM
                    accountcore_accounts_balance
                WHERE
                    year*12+month >= %s*12+%s AND year*12+month<=%s*12+%s
                    AND
                    org in %s
                GROUP BY
                    org,account,items
                ORDER BY
                    org,account,items)
        AS t
        LEFT OUTER JOIN  accountcore_account as t2 
        ON t.account_id =t2.id
        LEFT OUTER JOIN (select t4.id as item_class_id,
                                t4.name as item_class_name, 
                                t3.id as item_id,
                                t3.number as item_number,
                                t3.name as item_name
                            from  accountcore_item as t3 
                            left outer join accountcore_itemclass as t4 
                            on  t3."itemClass"=t4.id) 
                            as t5
        ON t.item_id=t5.item_id
        WHERE t.account_id in %s '''
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()


class Balance(object):
    '''一条余额记录'''

    def __init__(self, org_id, account_id, item_id):
        self.org_id = org_id
        self.account_class_id = 0
        self.account_father_id = ""
        self.account_id = account_id
        self.account_number = ""
        self.account_name = ""
        self.direction = None
        self.item_class_id = 0
        self.item_class_name = ""
        self.item_id = item_id
        self.item_number = ""
        self.item_name = ""
        self.beginingDamount = 0
        self.beginingCamount = 0
        self.damount = 0
        self.camount = 0
        self.org_account_item = str(org_id)+"." + \
            str(account_id)+"-"+str(item_id)


class Balances(object):
    '''余额记录的明细容器'''

    def __init__(self):
        pass
        self.org_account_items = {}

    def add(self, balance):
        '''添加一行余额记录'''
        mark = str(balance.org_id)+'.'+str(balance.account_id) + \
            "-"+str(balance.item_id)
        self.org_account_items.update({mark: balance})

    def exit(self, org_id, account_id, item_id):
        '''存在相同科目和和核算项目的余额'''
        org_account_item = str(org_id)+"."+str(account_id)+"-"+str(item_id)
        if org_account_item in self.org_account_items:
            return True
        return False

    def exitAccount(self, accountId):
        '''存在相同科目的余额'''
        if accountId in self.accounts:
            return True
        return False

    def sorted(self):
        self.accounts = sorted(self.accounts.items, key=lambda x: x[0])
        self.org_account_items = sorted(
            self.org_account_items, key=lambda x: x[0])
