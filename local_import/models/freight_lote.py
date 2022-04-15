# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Lote(models.Model):
    _inherit = "freight.operation"

    impor_regimen = fields.Many2one('freight.import.regimen', string="Import Regimen")
    aforo_types = fields.Many2one('freight.aforo.types', string="Aforo Types")

    compras_line_ids = fields.One2many('purchase.order', 'lote_impt')
    compras_ibv = fields.Integer(compute = "_compute_compras_ibv")

    piking_line_ids = fields.One2many('stock.picking','lote_impt')
    pickin_ibv = fields.Integer(compute="_compute_invbl")

    invoice_line_ids = fields.One2many('account.move','lote_impot')
    invoice_ibv = fields.Integer(compute="_compute_invoice_ibv")

    costes = fields.Many2one('stock.landed.cost')

    def _compute_invbl(self):
        for rec in self:
            if rec.piking_line_ids.state == "done":
                self.pickin_ibv = 1
            else:
                self.pickin_ibv = 0

    def _compute_compras_ibv(self):
        for re in self:
            if re.compras_line_ids.state == "purchase":
                re.compras_ibv = 1
            else:
                re.compras_ibv = 0

    def _compute_invoice_ibv(self):
        for re in self:
            if re.invoice_line_ids.state == "posted":
                re.invoice_ibv = 1
            else:
                re.invoice_ibv = 0

    def button_link_costes_destino(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.landed.cost',
            'name': 'Entrevista',
            'context':{'default_lote_id':self.id},
            'view_mode': 'form',
            'target': 'new',
        }