# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMStage(models.Model):
    _inherit = "fsm.stage"

    @api.model
    def _default_sub_stage(self):
        # limit=1 guards against duplicate names
        return self.env["fsm.stage.status"].search([("name", "=", "Default")], limit=1)

    sub_stage_id = fields.Many2one(
        "fsm.stage.status",
        string="Default Sub-Status",
        default=_default_sub_stage,
    )

    sub_stage_ids = fields.Many2many(
        "fsm.stage.status",
        "fsm_sub_stage_rel",
        "fsm_stage_id",
        "sub_stage_id",
        string="Potential Sub-Statuses",
    )

    @api.model
    def _init_substatus_defaults(self):
        default = self.env.ref(
            'fieldservice_substatus.fsm_stage_status_default',
            raise_if_not_found=False,
        )
        if default:
            self.search([('sub_stage_id', '=', False)]).write({'sub_stage_id': default.id})

    @api.onchange("sub_stage_id")
    def onchange_sub_stage_id(self):
        if self.sub_stage_id:
            self.sub_stage_ids = self.sub_stage_id