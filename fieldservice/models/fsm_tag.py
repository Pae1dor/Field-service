# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class FSMTag(models.Model):
    _name = "fsm.tag"
    _description = "Field Service Tag"
    _order = "name"

    name = fields.Char(required=True)
    parent_id = fields.Many2one("fsm.tag", string="Parent", index=True)
    color = fields.Integer(string="Color Index", default=10)
    full_name = fields.Char(
        compute="_compute_full_name", store=True, recursive=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company related to this tag",
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "Tag name must be unique per company.",
        ),
    ]

    @api.depends("name", "parent_id.full_name")
    def _compute_full_name(self):
        for rec in self:
            if rec.parent_id:
                rec.full_name = f"{rec.parent_id.full_name}/{rec.name}"
            else:
                rec.full_name = rec.name

    @api.constrains("parent_id")
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("Cannot create recursive tag hierarchy."))