# Copyright (C) 2019 - TODAY, Open Source Integrators, Brian McMaster
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.osv import expression


class FSMStageStatus(models.Model):
    _name = "fsm.stage.status"
    _description = "Order Sub-Status"

    name = fields.Char(required=True)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        context = self.env.context

        if context.get("fsm_order_stage_id"):
            stage_id = self.env["fsm.stage"].browse(context.get("fsm_order_stage_id"))
            sub_stage_ids = stage_id.sub_stage_id + stage_id.sub_stage_ids

            if sub_stage_ids:
                # AND this condition with the incoming domain (in case of Search)
                new_domain = [("id", "in", sub_stage_ids.ids)]
                domain = expression.AND([domain, new_domain])

        return super()._search(domain, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)