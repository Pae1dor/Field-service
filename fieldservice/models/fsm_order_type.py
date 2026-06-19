# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FSMOrderType(models.Model):
    _name = "fsm.order.type"
    _description = "Field Service Order Type"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    internal_type = fields.Selection(
        selection=[("fsm", "FSM"), ("repair", "Repair"), ("maintenance", "Maintenance")],
        default="fsm",
        required=True,
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Order type name must be unique."),
    ]