# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RPartner(models.Model):
    _inherit = "res.partner"

    import_opt = fields.Boolean(string="Import")