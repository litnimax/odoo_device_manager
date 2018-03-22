# -*- coding: utf-8 -*-
from odoo import http

# class Container(http.Controller):
#     @http.route('/container/container/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/container/container/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('container.listing', {
#             'root': '/container/container',
#             'objects': http.request.env['container.container'].search([]),
#         })

#     @http.route('/container/container/objects/<model("container.container"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('container.object', {
#             'object': obj
#         })