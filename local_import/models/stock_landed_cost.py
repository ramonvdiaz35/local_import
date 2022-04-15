# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    lote_id = fields.Many2one('freight.operation',string="Lote")

    # @api.model
    # def default_get(self, fields):
    #     res = super(StockLandedCost, self).default_get(fields)
    #     self.lote_id = self._context.get('active_id')
    #     return res

    # @api.onchange('lote_id')
    # def _onchange_paciente_id(self):
    #     for rec in self:
    #         if rec.lote_id.id:
    #             trasferencia = self.env['stock.picking'].search([('lote_impt.id', '=', self.lote_id.id)])
    #             rec.picking_ids = trasferencia
    #         else:
    #             print("Desde Costes en destino")

    @api.onchange('lote_id')
    def _onchange_lote_id(self):
        for rec in self:
            if self.lote_id.id:
                trasferencia = self.env['stock.picking'].search([('lote_impt.id', '=', self.lote_id.id)])
                rec.picking_ids = trasferencia

    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        picking = self.env['stock.picking'].search([('lote_impt.id','=',self.lote_id.id)])
        print("ok")
        print(picking)
