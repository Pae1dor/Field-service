from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FsmPmSchedule(models.Model):
    _name = 'fsm.pm.schedule'
    _description = 'PM Schedule / Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'next_pm_date'

    name = fields.Char(string='PM Plan Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    location_id = fields.Many2one('fsm.location', string='Location', required=True)
    equipment_id = fields.Many2one('fsm.equipment', string='Equipment')
    team_id = fields.Many2one('fsm.team', string='FSM Team', required=True)

    frequency_id = fields.Many2one(
        'fsm.pm.frequency', string='Frequency', required=True, tracking=True,
    )

    advance_days = fields.Integer(
        string='Advance Notice (Days)', default=5,
        help='SMS notification sent to customer and technician ahead of the job date',
    )

    last_pm_date = fields.Date(string='Last PM Date', tracking=True)
    next_pm_date = fields.Date(
        string='Next PM Date',
        compute='_compute_next_pm_date',
        store=True,
    )

    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], default='active', string='Status', tracking=True)

    order_ids = fields.One2many('fsm.order', 'pm_schedule_id', string='Service Orders')
    order_count = fields.Integer(compute='_compute_order_count', string='Order Count')

    description = fields.Text(string='PM Job Details')

    @api.depends('last_pm_date', 'frequency_id', 'frequency_id.months')
    def _compute_next_pm_date(self):
        for rec in self:
            if rec.last_pm_date and rec.frequency_id:
                rec.next_pm_date = rec.last_pm_date + relativedelta(months=rec.frequency_id.months)
            else:
                rec.next_pm_date = False

    @api.depends('order_ids')
    def _compute_order_count(self):
        for rec in self:
            rec.order_count = len(rec.order_ids)

    def action_generate_order(self):
        """Create FSM Order from PM Schedule with advance-notice SMS."""
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('PM plan "%s" is inactive.') % self.name)

        pm_type = self.env['fsm.service.type'].search([('code', '=', 'pm')], limit=1)
        order = self.env['fsm.order'].create({
            'location_id': self.location_id.id,
            'team_id': self.team_id.id,
            'service_type_id': pm_type.id,
            'pm_schedule_id': self.id,
            'equipment_id': self.equipment_id.id if self.equipment_id else False,
            'description': (
                f'[PM Auto] {self.name}\n'
                f'Frequency: {self.frequency_id.name or ""}\n'
                f'{self.description or ""}'
            ),
            'scheduled_date_start': fields.Datetime.now(),
        })
        order._send_sms_notification(
            f'[PM Advance Notice] PM job "{self.name}" scheduled for {self.next_pm_date}. '
            f'Technician will contact you {self.advance_days} day(s) in advance.'
        )
        return {
            'type': 'ir.actions.act_window',
            'name': 'FSM Order',
            'res_model': 'fsm.order',
            'res_id': order.id,
            'view_mode': 'form',
        }

    def action_view_orders(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Service Orders',
            'res_model': 'fsm.order',
            'domain': [('pm_schedule_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_pm_schedule_id': self.id},
        }
        if self.order_count == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.order_ids[0].id
        return action

    def action_deactivate(self):
        self.write({'state': 'inactive'})

    def action_activate(self):
        self.write({'state': 'active'})

    @api.model
    def _cron_generate_pm_orders(self):
        """Cron job: automatically generates PM Orders when the advance-notice date is reached."""
        today = date.today()
        schedules = self.search([('state', '=', 'active'), ('next_pm_date', '!=', False)])
        for sched in schedules:
            trigger_date = sched.next_pm_date - relativedelta(days=sched.advance_days)
            if trigger_date > today:
                continue
            # Avoid duplicate creation: check for an order still open in this cycle
            existing = self.env['fsm.order'].search([
                ('pm_schedule_id', '=', sched.id),
                ('is_closed', '=', False),
            ], limit=1)
            if not existing:
                sched.action_generate_order()
