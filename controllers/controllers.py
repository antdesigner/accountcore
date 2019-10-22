# -*- coding: utf-8 -*-
from odoo import http
import random

class FormulaController(http.Controller):
    @http.route('/ac/compute', type='json', auth='none')
    def compute(self, **kw):
        a=random.randint(0,100)
        return a
