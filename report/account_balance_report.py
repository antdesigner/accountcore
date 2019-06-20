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
        test = 'hello'
        return {
            'doc_ids': docids,
            'doc_model': self.env['accountcore.accounts_balance'],
            'data': data,
            'test': test
        }
