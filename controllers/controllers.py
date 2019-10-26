# -*- coding: utf-8 -*-
import random
from functools import partial
from ..models.ac_obj import Structure
from ..models.ac_period import Period, VoucherPeriod
from odoo import http
from odoo.http import request


class FormulaController(http.Controller):
    @http.route('/ac/compute', type='http', auth='user', csrf=False)
    def compute(self, formula, startDate, endDate, orgIds):

        org_ids = self.wapBydot(orgIds)
        startDate = self.wapBydot(startDate)
        endDate = self.wapBydot(endDate)

        accountAmount = 'self.accountAmount(' + \
            org_ids+","+startDate+","+endDate+","
        tactics = [('account(', accountAmount)]
        newFormula = self.rebuildFormula(formula, tactics)

        self.env = request.env
        result = eval(newFormula)

        return str(result)

    def test(self, a, b):

        return a+b

    def accountAmount(self, org_ids, start_date, end_data, accountName, hasChild, amountType, itemsName):
        orgIds = org_ids.split("/")
        org_ids = list(map(int, orgIds))
        orgs = self.env['accountcore.org'].sudo().browse(org_ids)

        itemsName = itemsName.split("/")
        items = self.env['accountcore.item'].sudo().search(
            [('name', 'in', itemsName)])

        account = self.env['accountcore.account'].sudo().search(
            [('name', '=', accountName)])

        period = Period(start_date, end_data)

        amount = 0

        for org in orgs:
            for item in items:
                amount += account.getEndAmount(org, item)

        return amount
    # 替换公式为内部名称，并插入更多参数

    def rebuildFormula(self, oldFormula, tactics):
        '''重建公式'''
        newFormula = oldFormula
        for item in tactics:
            newFormula = newFormula.replace(item[0], item[1])
        return newFormula

    def wapBydot(self, o):
        '''用单引号包裹对象'''
        return "'"+str(o)+"'"
