# Copyright (C) 2020 Brian McMaster
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class FSMPersonCalendarFilter(models.Model):
    """Assigned Worker Calendar Filter"""

    _name = "fsm.person.calendar.filter"
    _description = "FSM Person Calendar Filter"

    user_id = fields.Many2one(
        "res.users",
        string="Me",
        required=True,
        default=lambda self: self.env.user,
        ondelete="cascade",
        index=True,
    )
    fsm_person_id = fields.Many2one(
        "fsm.person",
        string="FSM Worker",
        required=True,
        ondelete="cascade",
        index=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "user_id_fsm_person_id_unique",
            "UNIQUE(user_id, fsm_person_id)",
            "You cannot have the same worker twice.",
        ),
    ]