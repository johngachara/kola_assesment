from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True,
                                  default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one(related='employee_id.department_id', string="Department", store=True)

    # Remove product fields from here as they'll be in the lines
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

    # New field for request lines
    line_ids = fields.One2many('purchase.request.line', 'request_id', string='Request Lines')

    # Link this request to RFQs - changed to One2many since multiple RFQs could be created
    rfq_ids = fields.One2many('purchase.order', 'purchase_request_id', string='RFQs')
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

        # Check if user is in procurement group
        if not self.env.user.has_group('kola_assignment.group_purchase_request_procurement'):
            raise AccessError(_("Only procurement can approve purchase requests."))

        if not self.line_ids:
            raise UserError(_("You cannot create an RFQ without products!"))

        # Create separate RFQ for each product
        purchase_orders = self.env['purchase.order']
        for line in self.line_ids:
            purchase_order = self.env['purchase.order'].create({
                'is_multi_vendor_rfq': True,
                'partner_id': self.env.user.company_id.id,
                'purchase_request_id': self.id,
                'date_order': fields.Datetime.now(),
                'origin': self.name,
                'order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': line.product_qty,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.product_id.standard_price,
                    'date_planned': self.expected_date or fields.Date.today(),
                })],
            })
            purchase_orders += purchase_order

        # Update the request state
        self.write({
            'state': 'rfq_created'
        })

        # If only one RFQ was created, show it
        if len(purchase_orders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Request for Quotation'),
                'res_model': 'purchase.order',
                'res_id': purchase_orders[0].id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            # Show the list of created RFQs
            return {
                'type': 'ir.actions.act_window',
                'name': _('Requests for Quotation'),
                'res_model': 'purchase.order',
                'domain': [('id', 'in', purchase_orders.ids)],
                'view_mode': 'list,form',
                'target': 'current',
            }


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    request_id = fields.Many2one('purchase.request', string='Purchase Request', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                                     related='product_id.uom_id')
    remarks = fields.Text(string='Remarks')



