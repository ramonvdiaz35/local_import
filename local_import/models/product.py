# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Product(models.Model):
    _inherit = "product.template"

    import_opt = fields.Boolean(string="Import")
