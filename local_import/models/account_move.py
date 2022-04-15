from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    lote_impot = fields.Many2one('freight.operation',string="Lote impt")





