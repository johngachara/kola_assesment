from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import float_is_zero


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vendor_ids = fields.Many2many(
        'res.partner',
        string='Vendors',
    )
    bid_ids = fields.One2many('purchase.bid', 'purchase_order_id', string='Bids')
    winning_bid_id = fields.Many2one('purchase.bid', string='Winning Bid')
    is_multi_vendor_rfq = fields.Boolean('Multi-Vendor RFQ', default=True)
    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request')
    parent_rfq_id = fields.Many2one('purchase.order', string='Parent RFQ')




    def action_send_to_multiple_vendors(self):
        if not  self.env.user.has_group('kola_assignment.group_purchase_request_procurement'):
            raise AccessError(_("Only procurement can send rfq's"))
        for order in self:
            if not order.vendor_ids:
                raise UserError(_("Please select vendors first!"))

            if not order.is_multi_vendor_rfq:
                raise UserError(_("Please select multi vendor RFQ to send to multiple vendors!"))

            # Create vendor-specific copies of the RFQ
            for vendor in order.vendor_ids:
                # Skip if the vendor is already the partner
                if vendor.id == order.partner_id.id:
                    continue

                # Create a copy of the RFQ for each additional vendor
                rfq_copy = order.copy({
                    'partner_id': vendor.id,
                    'origin': order.name,  # Reference to the original RFQ
                    'is_multi_vendor_rfq': False,  # Since This is a child RFQ
                    'parent_rfq_id': order.id
                })

        return True

    def select_winning_bid(self):
        if not  self.env.user.has_group('kola_assignment.group_purchase_request_procurement'):
            raise AccessError(_("Only procurement can select the winning bid"))
        for order in self:
            if not order.bid_ids:
                raise UserError(_("No bids received yet!"))
            valid_bids = order.bid_ids.filtered(lambda b: b.bid_amount > 0)
            sorted_bids = valid_bids.sorted(key=lambda b: b.bid_amount)

            if not sorted_bids:
                raise UserError(_("No valid bids found (all are zero)!"))

            # Select the lowest bid as winner
            order.winning_bid_id = sorted_bids[0]

            # Create actual purchase order from winning bid
            po_vals = {
                'partner_id': order.winning_bid_id.vendor_id.id,
                'date_order': fields.Datetime.now(),
                'origin': order.name,
                'purchase_request_id': order.purchase_request_id.id,
            }
            po = self.env['purchase.order'].create(po_vals)

            # Copy order lines with bid price
            for line in order.order_line:
                line_price = 0
                if line.product_qty:
                    line_price = order.winning_bid_id.bid_amount / line.product_qty

                line_vals = {
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_qty': line.product_qty,
                    'product_uom': line.product_uom.id,
                    'price_unit': line_price,
                    'date_planned': line.date_planned,
                }
                self.env['purchase.order.line'].create(line_vals)

            # Confirm the PO
            po.button_confirm()

            # Update the status of this RFQ
            order.write({'state': 'done'})

            return {
                'type': 'ir.actions.act_window',
                'name': _('Purchase Order'),
                'res_model': 'purchase.order',
                'res_id': po.id,
                'view_mode': 'form',
                'target': 'current',
            }