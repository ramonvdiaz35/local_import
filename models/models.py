# -*- coding: utf-8 -*-

from itertools import groupby
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'ProductTemplate'

    import_field = fields.Boolean(
        string='Import_field',
        required=False)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'ResPartner'

    import_field = fields.Boolean(
        string='Import_field',
        required=False)


class ImportRegime(models.Model):
    _name = 'import.regime'
    _description = 'ImportRegime'

    name = fields.Char()

    date = fields.Date(
        string='Date',
        required=False)
    type = fields.Char(
        string='Type',
        required=False)
    active = fields.Boolean(
        string='Active',
        required=False)


class TypesAforo(models.Model):
    _name = 'types.aforo'
    _description = 'TypesAforo'

    name = fields.Char(string='Name')
    active = fields.Boolean(
        string='Active',
        required=False)


class FreightOperation(models.Model):
    _inherit = 'freight.operation'
    _description = 'FreightOperation'

    name = fields.Char(string='Lote')

    import_regime_id = fields.Many2one(
        comodel_name='import.regime',
        string='Import Regime',
        required=False)

    types_aforo_id = fields.Many2one(
        comodel_name='types.aforo',
        string='Types Aforo',
        required=False)

    purchase_order_ids = fields.One2many(
        comodel_name='purchase.order',
        inverse_name='lote_import_id',
        string='Purchase Order Lote',
        domain=lambda self: [('state', '=', 'purchase')],
        required=False)

    stock_picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='lote_import_id',
        string='Stock Picking',
        domain=lambda self: [('state', '=', 'done')],
        required=False)

    account_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='lote_import_id',
        string='Account Move',
        domain=lambda self: [('state', '=', 'posted')],
        required=False)

    account_payment_ids = fields.One2many(
        comodel_name='account.payment',
        inverse_name='lote_import_id',
        string='Account Payment',
        compute='_compute_account_payment_ids',
        required=False)

    stock_landed_cost_ids = fields.One2many(
        comodel_name='stock.landed.cost',
        inverse_name='freight_operation_id',
        string='Landed Cost',
        # domain=lambda self: [('state', '=', 'posted')],
        compute='_compute_stock_landed_cost_ids',
        required=False)

    def open_landed_cost_form_view(self):
        try:
            form_view_id = self.env.ref('stock_landed_costs.view_stock_landed_cost_form').id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Action Name',
            'context': {'default_freight_operation_id': self.id},
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.landed.cost',
            'views': [(form_view_id, 'form')],
            'target': 'current',
        }

    @api.model
    def create(self, values):

        values['operation'] = 'master'
        return super(FreightOperation, self).create(values)

    @api.depends('account_move_ids')
    def _compute_account_payment_ids(self):
        list_id = []

        if self.account_move_ids:
            for move in self.account_move_ids:
                obj_payment = self.env['account.payment'].search([('partner_id.id', '=', move.partner_id.id)])
                for pay in obj_payment:
                    for inv in pay.reconciled_bill_ids:
                        if move.id == inv.id:
                            list_id.append(pay.id)
            self.update({
                'account_payment_ids': [(6, 0, list_id)]
            })
        else:
            self.account_payment_ids = None

    @api.depends('account_move_ids')
    def _compute_stock_landed_cost_ids(self):
        list_id = []
        obj_stock_landed_cost = self.env['stock.landed.cost'].search([('freight_operation_id', '=', self.id)])
        if obj_stock_landed_cost:
            for landed_cost in obj_stock_landed_cost:
                list_id.append(landed_cost.id)
            self.update({
                'stock_landed_cost_ids': [(6, 0, list_id)]
            })
        else:
            self.stock_landed_cost_ids = None


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'PurchaseOrder'

    lote_import_id = fields.Many2one(
        comodel_name='freight.operation',
        string='Lote Imp',
        required=False)
    import_field = fields.Boolean(related='partner_id.import_field', string='Import field')

    @api.onchange('order_line')
    def _onchange_order_line(self):
        if self.import_field:
            for line in self.order_line:
                if not line.product_id.import_field:
                    raise UserError(_('El producto debe ser de importación.'))

    def button_confirm(self):
        for order in self:
            if order.import_field:
                if not order.lote_import_id:
                    raise UserError(_('Debe agregar el lote antes de confirmar la orden .'))

            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.company.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'default_lote_import_id': self.lote_import_id.id,
        })

        return super(PurchaseOrder, self).action_create_invoice()


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = 'StockPicking'

    lote_import = fields.Char(
        string='Lote Imp',
        required=False,
        compute='_compute_lote_import')

    lote_import_id = fields.Many2one(
        comodel_name='freight.operation',
        string='Lote Imp id',
        required=False)

    @api.depends('origin')
    def _compute_lote_import(self):
        if self.origin:
            obj_purchase_order = self.env['purchase.order'].search([('name', '=', self.origin)])
            self.lote_import = obj_purchase_order.lote_import_id.name
            self.lote_import_id = obj_purchase_order.lote_import_id

        else:
            self.lote_import = ''
            self.lote_import_id = None


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'AccountMove'

    lote_import = fields.Char(
        string='Lote Imp',
        required=False,
        compute='_compute_lote_import')

    lote_import_id = fields.Many2one(
        comodel_name='freight.operation',
        string='Lote Imp',
        required=False)

    @api.depends('invoice_line_ids')
    def _compute_lote_import(self):
        if self.invoice_line_ids:
            self.lote_import = self.invoice_line_ids[0].purchase_order_id.lote_import_id.name
            self.lote_import_id = self.invoice_line_ids[0].purchase_order_id.lote_import_id
        else:
            self.lote_import = ''
            self.lote_import_id = None

    def action_post(self):
        if not self.lote_import_id:
            raise UserError(_('Debe agregar el lote antes de confirmar la orden .'))
        return self._post(soft=False)


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'AccountPayment'

    lote_import_id = fields.Many2one(
        comodel_name='freight.operation',
        string='Lote Imp',
        required=False)


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    _description = 'StockLandedCost'

    freight_operation_id = fields.Many2one(
        comodel_name='freight.operation',
        string='Lote',
        required=False)

    lote_import_id = fields.Many2one(
        comodel_name='freight.operation',
        string='Lote Imp',
        required=False)

    @api.onchange('picking_ids')
    def _onchange_picking_ids(self):
        for picking in self.picking_ids:
            if self.search_picking(picking):

                break
            else:
                self.freight_operation_id = picking.lote_import_id

    @api.onchange('freight_operation_id')
    def _onchange_freight_operation_id(self):

        obj_freight_operation = self.env['freight.operation'].search(
            [('id', '=', self.freight_operation_id._origin.id)])

        picking_list_ids = self.search_and_remove_picking(obj_freight_operation)

        self.picking_ids = [(6, 0, [])]
        self.update({
            'picking_ids': picking_list_ids
        })
        if self.freight_operation_id._origin.id:
            if len(picking_list_ids) == 0:
                self.freight_operation_id = None
                raise ValidationError(
                    _('No existen recepciones disponibles para aplicar costos'))
            else:
              self.gen_detail()

    def gen_detail(self):

        self.cost_lines = [(6, 0, [])]
        data_list = []
        if self.freight_operation_id:
            for move in self.freight_operation_id.account_move_ids:
                for line in move.invoice_line_ids:
                    if line.product_id.type == 'service' and line.product_id.landed_cost_ok == True:

                        if line.product_id.split_method_landed_cost:
                            default_split_method = line.product_id.split_method_landed_cost
                        else:
                            default_split_method = 'equal'
                        accounts_data = line.product_id.product_tmpl_id.get_product_accounts()

                        data_list.append((0, 0, {
                            'name': line.product_id.name,
                            'product_id': line.product_id.id or '',
                            'account_id': accounts_data['stock_input'],
                            'price_unit': line.price_unit or 0.0,
                            'split_method': default_split_method,

                        }))
        self.update({'cost_lines': data_list})

        return True

    def search_and_remove_picking(self, obj_freight_operation):
        original_list_picking = obj_freight_operation.stock_picking_ids.ids
        picking_id_list = []

        obj_landed_cost = self.env['stock.landed.cost'].search(
            [('freight_operation_id.id', '=', obj_freight_operation.id)])
        for landed_cost in obj_landed_cost:
            for picking in obj_freight_operation.stock_picking_ids:
                if picking.id in landed_cost.picking_ids.ids:
                    picking_id_list.append(picking.id)

        for picking in picking_id_list:
            if picking in original_list_picking:
                original_list_picking.remove(picking)

        return original_list_picking

    def search_picking(self, picking):
        flag = False
        obj_landed_cost = self.env['stock.landed.cost'].search(
            [('freight_operation_id.id', '=', picking.lote_import_id.id)])
        for landed_cost in obj_landed_cost:
            if picking._origin.id in landed_cost.picking_ids.ids:
                flag = True
            return flag

    @api.depends('company_id')
    def _compute_allowed_picking_ids(self):
        self.env.cr.execute("""SELECT sm.picking_id, sm.company_id
                                    FROM stock_move AS sm
                              INNER JOIN stock_valuation_layer AS svl ON svl.stock_move_id = sm.id
                                   WHERE sm.picking_id IS NOT NULL AND sm.company_id IN %s
                                GROUP BY sm.picking_id, sm.company_id""", [tuple(self.company_id.ids)])
        valued_picking_ids_per_company = defaultdict(list)
        for res in self.env.cr.fetchall():
            valued_picking_ids_per_company[res[1]].append(res[0])
        for cost in self:
            if self.freight_operation_id:
                cost.allowed_picking_ids = self.search_allowed_picking_for_lote(self.freight_operation_id)
            else:
                cost.allowed_picking_ids = valued_picking_ids_per_company[cost.company_id.id]

    def search_allowed_picking_for_lote(self, obj_freight_operation):

        original_list_picking = obj_freight_operation.stock_picking_ids.ids
        picking_id_list = []

        obj_landed_cost = self.env['stock.landed.cost'].search(
            [('freight_operation_id.id', '=', obj_freight_operation.id)])

        for landed_cost in obj_landed_cost:
            for picking in obj_freight_operation.stock_picking_ids:
                if picking.id in landed_cost.picking_ids.ids:
                    picking_id_list.append(picking.id)

        for picking in picking_id_list:
            if picking in original_list_picking:
                original_list_picking.remove(picking)

        return original_list_picking

