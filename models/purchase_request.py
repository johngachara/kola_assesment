from email.policy import default

from odoo import models, fields, api,_
from odoo.exceptions import UserError,AccessError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', string="Department", store=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                                     related='product_id.uom_id')
    justification = fields.Text(string='Justification', required=True)
    date_request = fields.Date(string='Request Date', default=fields.Date.today)
    expected_date = fields.Date(string='Expected Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('rfq_created', 'RFQ Created'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft')

    # Link this request to an RFQ
    rfq_id = fields.Many2one('purchase.order', string='RFQ')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'
        return super(PurchaseRequest, self).create(vals)

    def action_confirm(self):
        if self.state != 'draft':
            raise UserError(_("Only draft requests can be confirmed!"))
        self.write({'state': 'confirmed'})

    def action_approve(self):
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed requests can be approved!"))
        self.write({'state': 'approved'})

    def action_reject(self):
        if self.state != 'draft':
            raise UserError(_("Only draft requests can be rejected!"))
        self.write({'state': 'rejected'})

    def create_rfq(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only approved requests can be converted to RFQs!"))

        # Check if user is in manager group or procurement group
        if not (self.env.user.has_group('kola_assignment.group_purchase_request_manager') or
                self.env.user.has_group('kola_assignment.group_purchase_request_procurement')):
            raise AccessError(_("Only managers can approve purchase requests."))
        # Create new RFQ
        purchase_order = self.env['purchase.order'].create({
            'is_multi_vendor_rfq': True,
            'partner_id': self.env.user.company_id.id,
            'purchase_request_id': self.id,
            'date_order': fields.Datetime.now(),
            'origin': self.name,
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'name': self.product_id.name,
                'product_qty': self.product_qty,
                'product_uom': self.product_uom_id.id,
                'price_unit': self.product_id.standard_price,
                'date_planned': self.expected_date or fields.Date.today(),
            })],
        })

        # Link RFQ to the request
        self.write({
            'rfq_id': purchase_order.id,
            'state': 'rfq_created'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Request for Quotation'),
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }