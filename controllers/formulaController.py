# -*- coding: utf-8 -*-
import random
from functools import partial
from ..models.ac_obj import ACTools
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
    def getAmount(self, account, org, item, period):
        '''期初余额'''
        amount = account.getBegingAmountOf(period.startP, org, item)
        return amount


# 期初借方余额
class ACMethod_beginingDamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''期初借方余额'''
        amount = account.getBegingDAmountOf(period.startP, org, item)
        return amount


# 期初贷方余额
class ACMethod_beginingCamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''期初贷方余额'''
        amount = account.getBegingCAmountOf(period.startP, org, item)
        return amount


# 借方发生额
class ACMethod_damount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''借方发生额'''
        start_p = period.startP
        end_p = period.endP
        amount = account.getDamountBetween(start_p, end_p, org, item)
        return amount


# 贷方发生额
class ACMethod_camount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''贷方发生额'''
        start_p = period.startP
        end_p = period.endP
        amount = account.getCamountBetween(start_p, end_p, org, item)
        return amount


# 期末余额
class ACMethod_endAmount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''期末余额'''
        amount = account.getEndAmountOf(period.endP, org, item)
        return amount


# 期末借方余额
class ACMethod_endDamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''期末借方余额'''
        amount = account.getEndDAmount(period.endP, org, item)
        return amount


# 期末贷方余额
class ACMethod_endCamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''期末贷方余额'''
        amount = account.getEndCAmount(period.endP, org, item)
        return amount


# 本年借方累计发生额
class ACMethod_cumulativeDamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''本年借方累计发生额'''
        endP = period.endP
        amount = account.getCumulativeDAmountOf(endP, org, item)
        return amount


# 本年贷方累计发生额
class ACMethod_cumulativeCamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''本年贷方累计发生额'''
        endP = period.endP
        amount = account.getCumulativeCAmountOf(endP, org, item)
        return amount


# 损益表本期实际发生额
class ACMethod_realHappend(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''损益表本期实际发生额'''
        return 1111


# 损益表本年实际发生额
class ACMethod_realHappendYear(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''损益表本年实际发生额'''
        return 1111


# 即时余额
class ACMethod_currentBalance(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''即时余额'''
        return account.getEndAmount(org, item)

# 即时本年借方累计


class ACMethod_currentCumulativeDamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''即时本年借方累计'''
        return account.getCurrentCumulativeDamount(org, item)

# 即时本年贷方方累计


class ACMethod_currentCumulativeCamount(ACMethodBace):
    def getAmount(self, account, org, item, period):
        '''即时本年贷方累计'''
        return account.getCurrentCumulativeCamount(org, item)


ACMethosContainer.addMethod(ACMethod_beginningBalance('期初余额'))
ACMethosContainer.addMethod(ACMethod_beginingDamount('期初借方余额'))
ACMethosContainer.addMethod(ACMethod_beginingCamount('期初贷方余额'))
ACMethosContainer.addMethod(ACMethod_damount('借方发生额'))
ACMethosContainer.addMethod(ACMethod_camount('贷方发生额'))
ACMethosContainer.addMethod(ACMethod_endAmount('期末余额'))
ACMethosContainer.addMethod(ACMethod_endDamount('期末借方余额'))
ACMethosContainer.addMethod(ACMethod_endCamount('期末贷方余额'))
ACMethosContainer.addMethod(ACMethod_cumulativeDamount('本年借方累计发生额'))
ACMethosContainer.addMethod(ACMethod_cumulativeCamount('本年贷方累计发生额'))
ACMethosContainer.addMethod(ACMethod_realHappend('损益表本期实际发生额'))
ACMethosContainer.addMethod(ACMethod_realHappendYear('损益表本年实际发生额'))
ACMethosContainer.addMethod(ACMethod_currentBalance('即时余额'))
ACMethosContainer.addMethod(ACMethod_currentCumulativeDamount('即时本年借方累计'))
ACMethosContainer.addMethod(ACMethod_currentCumulativeCamount('即时本年贷方累计'))


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

        account = self.env['accountcore.account'].sudo().search(
            [('name', '=', accountName)])
        accounts = [account]
        if hasChild.lower() == "true":
            accounts = account.getMeAndChilds()

        items = []
        if len(itemsName) != 0:
            itemsName = itemsName.split("/")
            items = self.env['accountcore.item'].sudo().search(
                [('name', 'in', itemsName)])

        period = Period(start_date, end_data)

        amount = ACTools.ZeroAmount()

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

    def getAmountOfType(self, account, org, item, amountType, period):
        '''根据不同的金额类型取数'''
        method = ACMethosContainer.getMethod(amountType)
        amount = ACTools.ZeroAmount()
        # 带有核算项目的科目，取全部核算项目

        if not item and account.accountItemClass:
            items = self.env['accountcore.item'].sudo().search(
                [('itemClass', '=', account.accountItemClass.id)])
            for itm in items:
                amount += ACTools.TranslateToDecimal(method.getAmount(account,
                                                                org,
                                                                itm,
                                                                period))

        else:
            amount = ACTools.TranslateToDecimal(method.getAmount(account,
                                                            org,
                                                            item,
                                                            period))
        return amount

    # 替换公式为内部名称，并插入更多参数
    def rebuildFormula(self, oldFormula, tactics):
        '''重建公式'''
        newFormula = oldFormula
        for item in tactics:
            newFormula = newFormula.replace(item[0], item[1])
        return newFormula
