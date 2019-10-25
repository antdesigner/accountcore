# -*- coding: utf-8 -*-
import random
from functools import partial
from ..models.ac_obj import Structure
from odoo import http
from odoo.http import request


class FormulaController(http.Controller):
    @http.route('/ac/compute', type='http', auth='user', csrf=False)
    def compute(self, formula):
        # accounts = request.env['accountcore.accounts']
        org_ids = self.wapBydot("[1,2,3]")
        startDate = self.wapBydot("2019-01-01")
        endDate = self.wapBydot("2019-01-01")
        accountAmount = 'self.accountAmount('+org_ids+","+startDate+","+endDate+","
        tactics = [('account(', accountAmount)]
        newFormula = self.rebuildFormula(formula, tactics)
        result=eval(newFormula)
        return str(result)

    def test(self, a, b):

        return a+b

    def accountAmount(self, org, start_data, end_data, account, hasChild, amountType, items):
        
        return 1

    def rebuildFormula(self, oldFormula, tactics):
        '''重建公式'''
        newFormula = oldFormula
        for item in tactics:
            newFormula = newFormula.replace(item[0], item[1])
        return newFormula

    def wapBydot(self, o):
        '''用单引号包裹对象'''
        return "'"+str(o)+"'"
