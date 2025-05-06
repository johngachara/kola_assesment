from odoo import models, fields,api,_
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class PurchaseBid(models.Model):
    _name = 'purchase.bid'
    _description = 'Purchase Bid'
    _rec_name = 'sequence'

    sequence = fields.Char(string='Bid Reference', required=True,
                           copy=False, readonly=True, default=lambda self: _('New'))
    purchase_order_id = fields.Many2one(
        'purchase.order', string='RFQ', required=True
    )
    vendor_id = fields.Many2one(
        'res.partner', string='Vendor', required=True, domain=[('supplier_rank', '>', 0)]
    )
    bid_amount = fields.Float(string='Bid Amount', required=True)
    bid_date = fields.Date(string='Bid Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('purchase.bid') or _('New')
        return super(PurchaseBid, self).create(vals)

    @api.constrains('bid_amount')
    def _check_bid_amount(self):
        for record in self:
            if float_is_zero(record.bid_amount, precision_digits=2):
                raise ValidationError(_('Bid amount must be greater than zero.'))

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_select(self):
        self.write({'state': 'selected'})
        # Set this bid as the winning bid on the RFQ
        self.purchase_order_id.winning_bid_id = self.id

    def action_reject(self):
        self.write({'state': 'rejected'})