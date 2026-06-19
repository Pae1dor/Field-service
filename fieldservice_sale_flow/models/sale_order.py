from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fsm_order_ids = fields.One2many('fsm.order', 'sale_id', string='FSM Orders')
    fsm_order_count = fields.Integer(compute='_compute_fsm_order_count', string='FSM Orders')

    @api.depends('fsm_order_ids')
    def _compute_fsm_order_count(self):
        for rec in self:
            rec.fsm_order_count = len(rec.fsm_order_ids)

    def action_create_fsm_order(self):
        self.ensure_one()
        team = self.env['fsm.team'].search(
            [('company_id', 'in', (self.company_id.id, False))], limit=1)
        if not team:
            raise UserError('No FSM Team found. Please create one first.')

        location = self.env['fsm.location'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not location:
            location = self.env['fsm.location'].create({
                'name': self.partner_id.name,
                'partner_id': self.partner_id.id,
                'owner_id': self.partner_id.id,
            })

        fsm_order = self.env['fsm.order'].create({
            'sale_id': self.id,
            'location_id': location.id,
            'team_id': team.id,
            'description': f'Repair job from {self.name}',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'FSM Order',
            'res_model': 'fsm.order',
            'res_id': fsm_order.id,
            'view_mode': 'form',
        }

    def action_view_fsm_orders(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Field Service Orders',
            'res_model': 'fsm.order',
            'domain': [('sale_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'default_sale_id': self.id},
        }
        if self.fsm_order_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.fsm_order_ids[0].id
        return action
