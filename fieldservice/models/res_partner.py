# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(selection_add=[("fsm_location", "Location")])
    fsm_location = fields.Boolean(string="Is a FS Location")
    fsm_person = fields.Boolean(string="Is a FS Worker")
    fsm_location_id = fields.One2many(
        comodel_name="fsm.location",
        inverse_name="partner_id",
        string="Related FS Location",
        readonly=True,
        limit=1,
    )
    service_location_id = fields.Many2one(
        "fsm.location", string="Primary Service Location"
    )
    owned_location_ids = fields.One2many(
        "fsm.location",
        "owner_id",
        string="Owned Locations",
        domain=[("fsm_parent_id", "=", False)],
    )
    owned_location_count = fields.Integer(
        compute="_compute_owned_location_count",
        string="# of Owned Locations",
    )

    @api.depends("owned_location_ids")
    def _compute_owned_location_count(self):
        Location = self.env["fsm.location"]
        for partner in self:
            partner.owned_location_count = Location.search_count(
                [("owner_id", "child_of", [partner.id])]
            )

    def action_open_owned_locations(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "fieldservice.action_fsm_location"
        )
        action["context"] = {}
        owned_locations = self.env["fsm.location"].search(
            [("owner_id", "child_of", [self.id])]
        )
        if len(owned_locations) == 1:
            action["views"] = [
                (
                    self.env.ref("fieldservice.fsm_location_form_view").id,
                    "form",
                )
            ]
            action["res_id"] = owned_locations.id
        else:
            action["domain"] = [("id", "in", owned_locations.ids)]
        return action

    def _convert_fsm_location(self):
        wiz = self.env["fsm.wizard"]
        partners_with_loc = (
            self.env["fsm.location"]
            .sudo()
            .search(
                [
                    ("active", "in", [False, True]),
                    ("partner_id", "in", self.ids),
                ]
            )
            .mapped("partner_id")
            .ids
        )
        partners_to_convert = self.filtered(
            lambda p: p.type == "fsm_location" and p.id not in partners_with_loc
        )
        for partner in partners_to_convert:
            wiz.action_convert_location(partner)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._convert_fsm_location()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._convert_fsm_location()
        return res