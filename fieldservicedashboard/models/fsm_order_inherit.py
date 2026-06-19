from odoo import models, fields


class FsmOrderInherit(models.Model):
    _inherit = 'fsm.order'

    dashboard_status = fields.Selection([
        ('new', 'Available / Awaiting Dispatch'),
        ('on_process', 'On Process / In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Technician Status (Dashboard)', default='new', tracking=True)

    technician_id = fields.Many2one('res.users', string='Technician')
