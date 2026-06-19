from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FsmPheUnit(models.Model):
    _name = 'fsm.phe.unit'
    _description = 'PHE Check Sheet - Unit'
    _order = 'order_id, unit_number'
    _inherit = ['mail.thread']

    order_id = fields.Many2one(
        'fsm.order', string='Service Order',
        ondelete='cascade', required=True, index=True,
    )
    unit_number = fields.Integer(string='Unit #', required=True, default=1)
    name = fields.Char(string='Unit Name', compute='_compute_name', store=True)

    state = fields.Selection([
        ('draft', 'Pending'),
        ('disassembled', 'Disassembled'),
        ('cleaned', 'Cleaned'),
        ('leak_tested', 'Leak Tested'),
        ('assembled', 'Reassembled'),
        ('done', 'Completed'),
    ], default='draft', string='Status', tracking=True)

    wash_location = fields.Selection([
        ('onsite', 'On-site (High-pressure)'),
        ('factory', 'Factory (Chemical/Ultrasonic)'),
    ], string='Wash Location')

    gasket_condition = fields.Selection([
        ('ok', 'Good - Reusable'),
        ('replaced', 'Replaced'),
    ], string='Gasket Condition')

    plate_leak = fields.Boolean(string='Plate Leak Found', default=False)
    plate_notes = fields.Text(string='Plate Leak Details (Plate No. / Unit)')
    plate_action = fields.Selection([
        ('replace', 'Order New Plate + PO'),
        ('accept', 'Customer Acknowledged (Disclaimer)'),
    ], string='Plate Leak Resolution')
    customer_notified = fields.Boolean(string='Customer Notified (SMS/Call/Portal)')

    leak_test_ok = fields.Boolean(string='Leak Test Passed')
    pressure_test_ok = fields.Boolean(string='Overall Pressure Test Passed')

    technician_id = fields.Many2one('fsm.person', string='Assigned Technician')
    date_completed = fields.Datetime(string='Completion Date', readonly=True)
    notes = fields.Text(string='Notes')

    @api.depends('unit_number')
    def _compute_name(self):
        for rec in self:
            rec.name = f'Unit #{rec.unit_number}'

    def action_disassemble(self):
        self.write({'state': 'disassembled'})
        self._post_state_note('Unit disassembled.')

    def action_clean(self):
        for rec in self:
            if not rec.wash_location:
                raise UserError(_('Unit #%s: Please specify wash location first.') % rec.unit_number)
        self.write({'state': 'cleaned'})
        self._post_state_note('Unit cleaning completed.')

    def action_leak_test(self):
        self.write({'state': 'leak_tested'})
        for rec in self:
            if rec.plate_leak:
                rec._post_state_note('Plate leak found - please notify customer and specify resolution.')
            else:
                rec._post_state_note('Leak test passed - no leak found.')

    def action_assemble(self):
        for rec in self:
            if rec.plate_leak and not rec.plate_action:
                raise UserError(
                    _('Unit #%s: Please specify plate leak resolution before reassembling.') % rec.unit_number
                )
            if not rec.gasket_condition:
                raise UserError(
                    _('Unit #%s: Please specify gasket condition.') % rec.unit_number
                )
        self.write({'state': 'assembled'})
        self._post_state_note('PHE reassembled (new gasket + bolts torqued).')

    def action_done(self):
        for rec in self:
            if not rec.pressure_test_ok:
                raise UserError(
                    _('Unit #%s: Pressure test not passed yet. Please test and confirm first.') % rec.unit_number
                )
        self.write({
            'state': 'done',
            'date_completed': fields.Datetime.now(),
        })
        self._post_state_note('Unit completed - pressure test passed.')

    def _post_state_note(self, msg):
        for rec in self:
            rec.order_id.message_post(
                body=_('[PHE %s] %s') % (rec.name, msg),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
