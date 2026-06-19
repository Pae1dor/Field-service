# Copyright (C) 2018 Brian McMaster
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMTeam(models.Model):
    _name = "fsm.team"
    _description = "Field Service Team"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    def _default_stages(self):
        return self.env["fsm.stage"].search(
            [("is_default", "=", True), ("stage_type", "=", "order")]
        )

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    color = fields.Integer(string="Color Index")
    sequence = fields.Integer(
        default=1, help="Used to sort teams. Lower is better."
    )
    stage_ids = fields.Many2many(
        "fsm.stage",
        "order_team_stage_rel",
        "team_id",
        "stage_id",
        string="Stages",
        default=lambda self: self._default_stages(),
    )
    order_ids = fields.One2many(
        "fsm.order",
        "team_id",
        string="Orders",
        domain=[("stage_id.is_closed", "=", False)],
    )
    order_count = fields.Integer(
        compute="_compute_order_counts", string="Orders Count"
    )
    order_need_assign_count = fields.Integer(
        compute="_compute_order_counts", string="Orders to Assign"
    )
    order_need_schedule_count = fields.Integer(
        compute="_compute_order_counts", string="Orders to Schedule"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company related to this team",
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "Team name must be unique per company.",
        ),
    ]

    @api.depends("order_ids.stage_id.is_closed",
                 "order_ids.person_id",
                 "order_ids.scheduled_date_start")
    def _compute_order_counts(self):
        Order = self.env["fsm.order"]
        for team in self:
            base = [
                ("team_id", "=", team.id),
                ("stage_id.is_closed", "=", False),
            ]
            team.order_count = Order.search_count(base)
            team.order_need_assign_count = Order.search_count(
                base + [("person_id", "=", False)]
            )
            team.order_need_schedule_count = Order.search_count(
                base + [("scheduled_date_start", "=", False)]
            )