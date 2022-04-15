# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError


class Compra(models.Model):
    _inherit = "purchase.order"

    lote_impt = fields.Many2one('freight.operation',string="Lote Impt")
    invbl = fields.Boolean()

    @api.onchange('partner_id')
    def _partner_id(self):
        if self.partner_id and self.partner_id.import_opt == True:
            self.invbl = True
        else:
            self.invbl = False

    def button_confirm(self):
        for order in self:
            if order.invbl:
                if not order.lote_impt:
                    raise ValidationError(_("No puede crear una ornden a este proveedor sin seleccionar un lote"))
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", self.partner_id.name))
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'user_id': False,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
            'lote_impt':self.lote_impt.id
        }

    # def action_create_invoice(self):
    #     rec = super(Compra,self).action_create_invoice()
    #     rec['context'] = {
    #         'default_move_type': 'in_invoice',
    #         'default_lote_impt': self.lote_impt.id,
    #     }
    #     print(rec['context'])
    #     return rec

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'lote_impot': self.lote_impt.id,
        }
        return invoice_vals

