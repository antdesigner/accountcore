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
        noShowNoAmount = form['noShowNoAmount']
        noShowZeroBalance = form['noShowZeroBalance']
        no_show_no_hanppend = form['no_show_no_hanppend']
        onlyShowOneLevel = form['onlyShowOneLevel']
        includeAccountItems = form['includeAccountItems']
        order_orgs = form['order_orgs']
        account_ids = form['account']
        org_id = form['org']
        orgs = self.env['accountcore.org'].sudo().browse(org_id)
        startDate = datetime.datetime.strptime(form['startDate'], '%Y-%m-%d')
        start_year = startDate.year
        start_month = startDate.month
        endDate = datetime.datetime.strptime(form['endDate'], '%Y-%m-%d')
        end_year = endDate.year
        end_month = endDate.month
        params = (start_year, start_month, end_year,
                  end_month, tuple(org_id))
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
            balance.beginingDamount = record['beginingDamount']
            balance.beginingCamount = record['beginingCamount']
            balance.item_class_name = record['item_class_name']
            balance.item_id = record['item_id']
            balance.item_name = record['item_name']
            balance.org_name = record['org_name']
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
                balance.item_class_name = balance_DAndCAmount['item_class_name']
                balance.item_id = balance_DAndCAmount['item_id']
                balance.item_name = balance_DAndCAmount['item_name']
                balance.org_name = balance_DAndCAmount['org_name']
                balances.add(balance)
                balance_DAndCAmount['havepre'] = True
                continue
        # 添加查询期间有发生额，但查询期间之前没有余额记录的相关科目记录
        for one in DandCAmounts:
            if one['havepre'] == False:
                # balance_current = Balance(
                #     temp_orgId, temp_accountId, temp_itemId)
                balance_current = Balance(
                    one['org_id'], one['account_id'], one['item_id'])
                balance_current.beginingDamount = 0
                balance_current.beginingCamount = 0
                balance_current.damount = one['damount']
                balance_current.camount = one['camount']
                balance_current.item_class_name = one['item_class_name']
                balance_current.item_id = one['item_id']
                balance_current.item_name = one['item_name']
                balance_current.org_name = one['org_name']
                # balance.damount = one['damount']
                # balance.camount = one['camount']
                # balance.item_class_name = one['item_class_name']
                # balance.item_id = one['item_id']
                # balance.item_name = one['item_name']
                # balance.org_name = one['org_name']
                balances.add(balance_current)
        balancesList = balances.getBalancesList()
        accountsArch = self._getAccountAcrch()
        accountsArchManager = AccountsArchManager(accountsArch, orgs)
        for balance in balancesList:
            accountArch = accountsArchManager.updateBy(balance)
            if balance.item_id:
                accountsArchManager.appendItem(accountArch, balance)
        accountsArchWithItems = accountsArchManager.getAccountArchWihtItems(
            AccountsArch_filter_org(org_id),
            AccountsArch_filter_accounts(account_ids),
            AccountsArch_filter_noShowNoAmount(noShowNoAmount),
            AccountsArch_filter_noShowZeroBalance(noShowZeroBalance),
            AccountsArch_filter_no_show_no_hanppend(no_show_no_hanppend),
            AccountsArch_filter_onlyShowOneLevel(onlyShowOneLevel),
            AccountsArch_filter_includeAccountItems(includeAccountItems),
            AccountsArch_filter_order_orgs(order_orgs))

        return {'doc_ids': docids, 'docs': accountsArchWithItems, 'data': data}

    def _getRecordsBeforStart(self, params):
        '''获得查询日期前的余额记录,已经按科目项目年份月份进行排序，方便取查询期间范围前的最近一期的余额记录'''
        query = ''' SELECT
                        year,
                        month,
                        org_id,
                        t_org.name as org_name,
                        account_id,
                        t_item.item_class_name,
                        item_id,
                        t_item.name as item_name,
                        "beginingDamount",
                        "beginingCamount"
                    FROM

                        (SELECT
                            year,
                            month,
                            org as org_id,
                            account as account_id,
                            items as item_id,
                            "beginingDamount",
                            "beginingCamount",
                            isbegining
                        FROM
                            accountcore_accounts_balance
                        WHERE
                            (year > %s
                            OR
                            year =%s AND month <= %s)
                            AND
                            org in %s) as t_accounts_balance
                    LEFT OUTER JOIN accountcore_item as t_item
                    ON t_accounts_balance.item_id=t_item.id
                    LEFT OUTER JOIN accountcore_org as t_org
                    ON t_accounts_balance.org_id=t_org.id
                    ORDER BY  org_id,account_id,item_id,year desc ,month desc,isbegining desc'''
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _getDAndCAmount(self, params):
        '''在查找期间的发生额'''
        # 当期借贷方发生额合计
        query = '''SELECT
                        org_id,
                        t_org.name as org_name,
                        account_id,
                        t_item.item_class_name,
                        item_id,
                        t_item.name as item_name,
                        damount,
                        camount,
                        havepre
                    FROM
                        (SELECT
                            org as org_id,
                            account as account_id,
                            items as item_id ,
                            sum(damount) as damount,
                            sum(camount)as camount,
                            False as havepre
                        FROM
                            accountcore_accounts_balance
                        WHERE
                            year*12+month >= %s*12+%s AND year*12+month<=%s*12+%s
                            AND
                            org in %s
                         GROUP BY org_id,account_id,item_id) AS t_accounts_balance
                    LEFT OUTER JOIN accountcore_item as t_item
                    ON t_accounts_balance.item_id=t_item.id
                    LEFT OUTER JOIN accountcore_org as t_org
                    ON t_accounts_balance.org_id=t_org.id
                    ORDER BY org_id,account_id,item_id'''
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _getAccountAcrch(self):
        '''获得科目表结构对象'''
        query = '''SELECT t_org.id as account_org_id,
                    t_org.name  as account_org_name,
                    null as org_id,
                    '' as org_name,
                    t_account."fatherAccountId" as account_father_id,
                    t_account_class.name as account_class_name,
                    t_account.id as account_id,
                    t_account.number as account_number,
                    t_account.name as account_name,
                    t_account.direction as direction,
                    0.0 as "beginingDamount",
                    0.0 as "beginingCamount",
                    0.0 as damount,
                    0.0 as camount
                FROM accountcore_account AS t_account
                LEFT OUTER JOIN accountcore_org as t_org
                ON t_account.org=t_org.id
                LEFT OUTER JOIN accountcore_accountClass as t_account_class
                ON t_account."accountClass"=t_account_class.id
                ORDER BY account_number'''
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()


class Balance(object):
    '''一条余额记录'''

    def __init__(self, org_id, account_id, item_id):
        self.org_id = org_id
        self.org_name = ""
        # self.account_class_id = 0
        self.account_father_id = ""
        self.account_id = account_id
        self.account_number = ""
        self.account_name = ""
        # self.direction = None
        # self.item_class_id = 0
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

    def keys(self):
        return ('org_id',
                'org_name',
                # 'account_class_id',
                # 'account_father_id',
                # 'account_id',
                # 'account_number',
                # 'account_name',
                # 'direction',
                # 'item_class_id',
                'item_class_name',
                'item_id',
                'item_number',
                'item_name',
                'beginingDamount',
                'beginingCamount',
                'damount',
                'camount',
                # 'org_account_item'
                )

    def __getitem__(self, item):
        return getattr(self, item)


class Balances(object):
    '''余额记录的明细容器'''

    def __init__(self):
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

    def getBalancesList(self):
        '''获得balance的列表形式'''
        return self.org_account_items.values()


class AccountsArchManager(object):
    '''科目余额管理器'''

    def __init__(self, accountsArch, orgs):
        self.accountsArch = []
        self.accountsArch_items = []
        for org in orgs:
            newAccountsArch = []
            for account in accountsArch:
                newAccount = account.copy()
                newAccount.update(
                    {'org_id': org.id, 'org_name': org.name})
                newAccountsArch.append(newAccount)
            self.accountsArch.extend(newAccountsArch)

    def updateBy(self, balance):
        accountArch = self._getAccountArchById(
            balance.account_id, balance.org_id)
        accountArch.addAmount(
            balance.beginingDamount,
            balance.beginingCamount,
            balance.damount,
            balance.camount)
        if accountArch.father_id:
            fatherAccount = self._getAccountArchById(
                accountArch.father_id, balance.org_id)
            fatherAccount.addAmount(
                balance.beginingDamount,
                balance.beginingCamount,
                balance.damount,
                balance.camount)
        return accountArch

    def _getAccountArchById(self, account_id, org_id):
        for line in self.accountsArch:
            if line['account_id'] == account_id and line['org_id'] == org_id:
                return AccountArch(line)

    def appendItem(self, accountArch, balance):
        accountArch_ = accountArch.copy()
        accountArch_.update(balance)
        self.accountsArch_items.append(accountArch_.account)

    def getAccountArchWihtItems(self, *filters):
        '''返回经过过滤排序后的科目余额记录'''
        self.accountsArch.extend(self.accountsArch_items)
        self.sortBy('account_number')
        for filter in filters:
            self.accountsArch = filter(self.accountsArch)
        return self.accountsArch

    def sortBy(self, field_str, reverse_it=False):
        '''根据某字段排序'''
        return self.accountsArch.sort(key=lambda t: t['account_number'], reverse=reverse_it)


class AccountsArch_filter_org(object):
    '''筛选机构'''

    def __init__(self, org_ids):
        self.__org_ids = org_ids

    def __call__(self, accountsArch):
        newAccountsArch = [
            a for a in accountsArch if a['org_id'] in self.__org_ids]
        return newAccountsArch


class AccountsArch_filter_accounts(object):
    '''筛选科目'''

    def __init__(self, account_ids):
        self.__account_ids = account_ids

    def __call__(self, accountsArch):
        newAccountsArch = [
            a for a in accountsArch if a['account_id'] in self.__account_ids]
        return newAccountsArch


class AccountsArch_filter_noShowNoAmount(object):
    '''无金额不显示'''

    def __init__(self, noShowNoAmount=True):
        self.__noShowNoAmount = noShowNoAmount

    def __call__(self, accountsArch):
        if self.__noShowNoAmount:
            newAccountsArch = [a for a in accountsArch if any(
                [(a['beginingDamount']-a['beginingCamount']) != 0, a['damount'] != 0, a['camount'] != 0])]
            return newAccountsArch
        else:
            return accountsArch


class AccountsArch_filter_noShowZeroBalance(object):
    '''余额为零不显示'''

    def __init__(self, noShowZeroBalance=True):
        self.__noShowZeroBalance = noShowZeroBalance

    def __call__(self, accountsArch):
        if self.__noShowZeroBalance:
            newAccountsArch = [a for a in accountsArch if (
                a['beginingDamount']+a['damount']-a['beginingCamount']-a['camount'] != 0)]
            return newAccountsArch
        else:
            return accountsArch


class AccountsArch_filter_no_show_no_hanppend(object):
    '''不显示无发生额的科目'''

    def __init__(self, no_show_no_hanppend=False):
        self.__no_show_no_hanppend = no_show_no_hanppend

    def __call__(self, accountsArch):
        if self.__no_show_no_hanppend:
            newAccountsArch = [
                a for a in accountsArch if a['damount'] != 0 or a['camount'] != 0]
            return newAccountsArch
        else:
            return accountsArch


class AccountsArch_filter_onlyShowOneLevel(object):
    '''只显示一级科目'''

    def __init__(self, onlyShowOneLevel=False):
        self.__onlyShowOneLevel = onlyShowOneLevel

    def __call__(self, accountsArch):
        if self.__onlyShowOneLevel:
            newAccountsArch = [
                a for a in accountsArch if not a['account_father_id'] and('item_id' not in a or not a['item_id'])]
            return newAccountsArch
        else:
            return accountsArch


class AccountsArch_filter_includeAccountItems(object):
    '''不显示核算项目'''

    def __init__(self, includeAccountItems=True):
        self.__includeAccountItems = includeAccountItems

    def __call__(self, accountsArch):
        if self.__includeAccountItems:
            return accountsArch
        else:
            newAccountsArch = [
                a for a in accountsArch if ('item_id' not in a or not a['item_id'])]
            return newAccountsArch


class AccountsArch_filter_order_orgs(object):
    '''多机构分开显示'''

    def __init__(self, order_orgs=True):
        self.__order_orgs = order_orgs

    def __call__(self, accountsArch):
        if self.__order_orgs:
            accountsArch.sort(key=lambda t: (t['org_id'], t['account_number']))
            return accountsArch

        else:
            return accountsArch


class AccountArch(object):
    '''科目余额管理器管理对象'''

    def __init__(self, account):
        self.account = account
        self.account_id = account['account_id']
        self.father_id = account['account_father_id']

    def addAmount(self, beginingDamount, beginingCamount, damount, camount):
        self.account['beginingDamount'] = (
            self.account['beginingDamount'] + beginingDamount)
        self.account['beginingCamount'] = (
            self.account['beginingCamount'] + beginingCamount)
        self.account['damount'] = self.account['damount']+damount
        self.account['camount'] = self.account['camount']+camount
        return self

    def copy(self):
        newAccount = self.account.copy()
        newAccountArch = AccountArch(newAccount)
        return newAccountArch

    def update(self, balance):
        self.account.update(dict(balance))
