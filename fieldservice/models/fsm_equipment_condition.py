from odoo import fields, models


class FsmEquipmentCondition(models.Model):
    _name = 'fsm.equipment.condition'
    _description = 'Equipment Condition'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)