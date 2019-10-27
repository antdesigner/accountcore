# -*- coding: utf-8 -*-
import random
from functools import partial
from ..models.ac_obj import Structure
from ..models.ac_period import Period, VoucherPeriod
from odoo import http
from odoo.http import request


class ACMethosContainer():
    _methods = {}

    @classmethod
    def addMethod(cls, method):
        cls._methods.update({method.name: method})

    @classmethod
    def getMethod(cls, methodName):
        method = cls._methods.get(methodName)
        return method


class ACMethodBace():
    def __init__(self, amountTypeName):
        self.name = amountTypeName

    def getAmount(self, account, org, item, period):
        pass


# 期初余额
class ACMethod_beginningBalance(ACMethodBace):
    '''期初余额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 期初借方余额
class ACMethod_beginingDamount(ACMethodBace):
    '''期初借方余额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 期初贷方余额
class ACMethod_beginingCamount(ACMethodBace):
    '''期初贷方余额'''

    def getAmount(self, account, org, item, period):
        return 111


# 借方发生额
class ACMethod_damount(ACMethodBace):
    '''借方发生额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 贷方发生额
class ACMethod_camount(ACMethodBace):
    '''贷方发生额'''

    def getAmount(self, account, org, item, period):
        return 1111

 # 期末余额


# 期末余额
class ACMethod_endAmount(ACMethodBace):
    '''期末余额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 期末贷方余额
class ACMethod_endDamount(ACMethodBace):
    '''期末贷方余额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 期末借方余额
class ACMethod_endCamount(ACMethodBace):
    '''期末借方余额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 本年借方累计发生额
class ACMethod_cumulativeDamount(ACMethodBace):
    '''本年借方累计发生额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 本年贷方累计发生额
class ACMethod_cumulativeCamount(ACMethodBace):
    '''本年贷方累计发生额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 损益表本期实际发生额
class ACMethod_realHappend(ACMethodBace):
    '''损益表本期实际发生额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 损益表本年实际发生额
class ACMethod_realHappendYear(ACMethodBace):
    '''损益表本年实际发生额'''

    def getAmount(self, account, org, item, period):
        return 1111


# 即时余额
class ACMethod_currentBalance(ACMethodBace):
    '''即时余额'''

    def getAmount(self, account, org, item, period):
        return account.getEndAmount(org, item)


ACMethosContainer.addMethod(ACMethod_beginningBalance('期初余额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('期初借方余额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('期初贷方余额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('借方发生额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('贷方发生额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('期末余额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('期末借方余额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('期末贷方余额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('本年借方累计发生额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('本年贷方累计发生额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('损益表本期实际发生额'))
ACMethosContainer.addMethod(ACMethod_beginningBalance('损益表本年实际发生额'))
ACMethosContainer.addMethod(ACMethod_currentBalance('即时余额'))


class FormulaController(http.Controller):
    @http.route('/ac/compute', type='http', auth='user', csrf=False)
    def compute(self, formula, startDate, endDate, orgIds):

        accountAmount = 'self.accountAmount(' + \
            orgIds+","+startDate+","+endDate+","
        tactics = [('account(', accountAmount)]
        newFormula = self.rebuildFormula(formula, tactics)

        self.env = request.env
        result = eval(newFormula)

        return str(result)

    def accountAmount(self, org_ids, start_date, end_data, accountName, hasChild, amountType, itemsName):
        orgIds = org_ids.split("/")
        org_ids = list(map(int, orgIds))
        orgs = self.env['accountcore.org'].sudo().browse(org_ids)

        items = []
        if len(itemsName) != 0:
            itemsName = itemsName.split("/")
            items = self.env['accountcore.item'].sudo().search(
                [('name', 'in', itemsName)])

        account = self.env['accountcore.account'].sudo().search(
            [('name', '=', accountName)])
        accounts = [account]
        if hasChild.lower() == "true":
            accounts = account.getMeAndChilds()

        period = Period(start_date, end_data)

        amount = 0

        for org in orgs:
            for ac in accounts:
                if len(items) == 0:
                    amount += self.getAmountOfType(ac,
                                                   org,
                                                   None,
                                                   amountType,
                                                   period)
                else:
                    for item in items:
                        amount += self.getAmountOfType(ac,
                                                       org,
                                                       item,
                                                       amountType,
                                                       period)

        return amount

    def getAmountOfType(self,
                        account,
                        org,
                        item,
                        amountType,
                        period):
        '''根据不同的金额类型取数'''
        method = ACMethosContainer.getMethod(amountType)
        amount = method.getAmount(account,
                                  org,
                                  item,
                                  period)
        return amount

    # 替换公式为内部名称，并插入更多参数
    def rebuildFormula(self, oldFormula, tactics):
        '''重建公式'''
        newFormula = oldFormula
        for item in tactics:
            newFormula = newFormula.replace(item[0], item[1])
        return newFormula
