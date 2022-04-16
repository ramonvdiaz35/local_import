# -*- coding: utf-8 -*-
# from odoo import http


# class LocalImport(http.Controller):
#     @http.route('/local_import/local_import/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/local_import/local_import/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('local_import.listing', {
#             'root': '/local_import/local_import',
#             'objects': http.request.env['local_import.local_import'].search([]),
#         })

#     @http.route('/local_import/local_import/objects/<model("local_import.local_import"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('local_import.object', {
#             'object': obj
#         })
