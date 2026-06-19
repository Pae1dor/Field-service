from odoo import models, fields, api
from odoo.exceptions import UserError


class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    sale_id = fields.Many2one('sale.order', string='Quotation / Sale Order', index=True, tracking=True)
    material_ids = fields.One2many('fsm.order.material', 'order_id', string='Materials / Parts')

    pr_count = fields.Integer(compute='_compute_counts', string='Purchase Requests')
    picking_count = fields.Integer(compute='_compute_counts', string='Stock Pickings')
    invoice_count = fields.Integer(compute='_compute_counts', string='Invoices')

    @api.depends('material_ids.purchase_request_id', 'material_ids.picking_id', 'sale_id.invoice_ids')
    def _compute_counts(self):
        for rec in self:
            rec.pr_count = len(rec.material_ids.mapped('purchase_request_id').filtered('id'))
            rec.picking_count = len(rec.material_ids.mapped('picking_id').filtered('id'))
            rec.invoice_count = len(rec.sale_id.invoice_ids) if rec.sale_id else 0

    # ── Material Request ────────────────────────────────────────────────

    def action_request_materials(self):
        self.ensure_one()
        draft_lines = self.material_ids.filtered(lambda l: l.state == 'draft' and l.product_id)
        if not draft_lines:
            raise UserError('No draft material lines to request.')

        stock_lines = draft_lines.filtered(lambda l: l.product_id.qty_available >= l.product_qty)
        pr_lines = draft_lines - stock_lines

        if stock_lines:
            self._create_stock_picking(stock_lines)
        if pr_lines:
            self._create_purchase_request(pr_lines)
        return True

    def _create_stock_picking(self, lines):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id)], limit=1)
        src_loc = warehouse.lot_stock_id if warehouse else self.env.ref('stock.stock_location_stock')
        dst_loc = self.env.ref('stock.location_production')
        picking_type = warehouse.out_type_id if warehouse else self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing'), ('company_id', '=', self.company_id.id)], limit=1)

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': src_loc.id,
            'location_dest_id': dst_loc.id,
            'origin': self.name,
            'move_ids': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': (line.product_uom_id or line.product_id.uom_id).id,
                'location_id': src_loc.id,
                'location_dest_id': dst_loc.id,
            }) for line in lines],
        })
        lines.write({'picking_id': picking.id, 'state': 'from_stock'})

    def _create_purchase_request(self, lines):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('company_id', '=', self.company_id.id)], limit=1)

        pr = self.env['purchase.request'].create({
            'origin': self.name,
            'picking_type_id': picking_type.id,
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_qty': line.product_qty,
                'product_uom_id': (line.product_uom_id or line.product_id.uom_id).id,
                'date_required': fields.Date.today(),
            }) for line in lines],
        })
        lines.write({'purchase_request_id': pr.id, 'state': 'pr_created'})

    # ── Smart Button Actions ────────────────────────────────────────────

    def action_view_pickings(self):
        self.ensure_one()
        picking_ids = self.material_ids.mapped('picking_id').filtered('id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Pickings',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', picking_ids)],
            'view_mode': 'list,form',
        }

    def action_view_pr(self):
        self.ensure_one()
        pr_ids = self.material_ids.mapped('purchase_request_id').filtered('id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Requests',
            'res_model': 'purchase.request',
            'domain': [('id', 'in', pr_ids)],
            'view_mode': 'list,form',
        }

    def action_view_sale(self):
        self.ensure_one()
        if not self.sale_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'res_id': self.sale_id.id,
            'view_mode': 'form',
        }

    # ── Invoice ────────────────────────────────────────────────────────

    def action_create_invoice(self):
        self.ensure_one()
        if not self.sale_id:
            raise UserError('No Quotation/Sale Order linked to this job.')
        if self.sale_id.state == 'draft':
            self.sale_id.action_confirm()
        self.sale_id._create_invoices()
        return self.sale_id.action_view_invoice()

    def action_view_invoices(self):
        self.ensure_one()
        if not self.sale_id:
            raise UserError('No Sale Order linked.')
        return self.sale_id.action_view_invoice()
