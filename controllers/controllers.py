# -*- coding: utf-8 -*-
from odoo import http

# class TigerAccountCore(http.Controller):
#     @http.route('/tiger_account_core/tiger_account_core/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tiger_account_core/tiger_account_core/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tiger_account_core.listing', {
#             'root': '/tiger_account_core/tiger_account_core',
#             'objects': http.request.env['tiger_account_core.tiger_account_core'].search([]),
#         })

#     @http.route('/tiger_account_core/tiger_account_core/objects/<model("tiger_account_core.tiger_account_core"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tiger_account_core.object', {
#             'object': obj
#         })