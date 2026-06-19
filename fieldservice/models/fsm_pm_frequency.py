from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FsmPmFrequency(models.Model):
    _name = 'fsm.pm.frequency'
    _description = 'PM Frequency'
    _order = 'months'

    name = fields.Char(required=True, translate=True)
    months = fields.Integer(required=True, default=1)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('months_positive', 'CHECK(months > 0)', 'Months must be positive.'),
    ]