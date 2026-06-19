from odoo import models, fields, api


class FsmOrderMaterial(models.Model):
    _name = 'fsm.order.material'
    _description = 'FSM Order Material Line'

    order_id = fields.Many2one('fsm.order', string='FSM Order', ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', default=1.0, required=True)
    product_uom_id = fields.Many2one('uom.uom', string='UoM')
    qty_available = fields.Float(string='On Hand', compute='_compute_qty_available', digits=(16, 2))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('from_stock', 'From Stock'),
        ('pr_created', 'PR Created'),
        ('done', 'Done'),
    ], default='draft', string='Status')
    picking_id = fields.Many2one('stock.picking', string='Stock Picking', readonly=True)
    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request', readonly=True)
    note = fields.Char(string='Note')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id

    @api.depends('product_id')
    def _compute_qty_available(self):
        for rec in self:
            rec.qty_available = rec.product_id.qty_available if rec.product_id else 0.0
