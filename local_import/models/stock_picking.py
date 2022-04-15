# -*- coding: utf-8 -*-
import sre_parse

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    lote_impt = fields.Many2one('freight.operation', string="Lote Impt")

