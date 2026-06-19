from odoo import fields, models


class FsmServiceType(models.Model):
    _name = 'fsm.service.type'
    _description = 'Field Service Type'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Service type code must be unique.'),
    ]