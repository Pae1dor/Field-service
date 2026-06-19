# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

AVAILABLE_PRIORITIES = [
    ("0", "Normal"),
    ("1", "Low"),
    ("2", "High"),
    ("3", "Urgent"),
]

HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class FSMStage(models.Model):
    _name = "fsm.stage"
    _description = "Field Service Stage"
    _order = "sequence, name, id"

    def _default_team_ids(self):
        default_team_id = self.env.context.get("default_team_id")
        return [default_team_id] if default_team_id else None

    active = fields.Boolean(default=True)
    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(
        default=1, help="Used to order stages. Lower is better."
    )
    legend_priority = fields.Text(
        string="Priority Management Explanation",
        translate=True,
        help="Explanation text to help users using the star and priority "
        "mechanism on stages or orders that are in this stage.",
    )
    fold = fields.Boolean(
        string="Folded in Kanban",
        help="This stage is folded in the kanban view when there are no "
        "record in that stage to display.",
    )
    is_closed = fields.Boolean(
        string="Is a close stage",
        help="Services in this stage are considered as closed.",
    )
    is_default = fields.Boolean(
        string="Is a default stage", help="Used as default stage"
    )
    custom_color = fields.Char(
        string="Color Code",
        default="#FFFFFF",
        help="Hex code only. Example: #FFFFFF",
    )
    description = fields.Text(translate=True)
    stage_type = fields.Selection(
        [
            ("order", "Order"),
            ("equipment", "Equipment"),
            ("location", "Location"),
            ("worker", "Worker"),
        ],
        string="Type",
        required=True,
        default="order",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    team_ids = fields.Many2many(
        "fsm.team",
        "order_team_stage_rel",
        "stage_id",
        "team_id",
        string="Teams",
        default=lambda self: self._default_team_ids(),
    )

    _sql_constraints = [
        (
            "type_sequence_uniq",
            "unique(stage_type, sequence, company_id)",
            "Stage type and sequence combination must be unique per company.",
        ),
    ]

    def get_color_information(self):
        return [
            {
                "color": stage.custom_color,
                "field": "stage_id",
                "opt": "==",
                "value": stage.name,
            }
            for stage in self.search([])
        ]

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    @api.constrains("custom_color")
    def _check_custom_color_hex_code(self):
        for rec in self:
            if rec.custom_color and not HEX_COLOR_RE.match(rec.custom_color):
                raise ValidationError(
                    _("Color code must be hex format. Example: #FFFFFF")
                )

    @api.constrains("is_default", "stage_type", "company_id")
    def _check_single_default(self):
        for rec in self:
            if not rec.is_default:
                continue
            duplicates = self.search(
                [
                    ("id", "!=", rec.id),
                    ("stage_type", "=", rec.stage_type),
                    ("is_default", "=", True),
                    ("company_id", "in", (rec.company_id.id, False)),
                ]
            )
            if duplicates:
                raise ValidationError(
                    _(
                        "Only one default stage allowed per type. "
                        "Existing default: %s"
                    )
                    % duplicates[0].name
                )