# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class FSMWizard(models.TransientModel):
    """A wizard to convert a res.partner record to a fsm.person or fsm.location."""

    _name = "fsm.wizard"
    _description = "FSM Record Conversion"

    fsm_record_type = fields.Selection(
        [("person", "Worker"), ("location", "Location")],
        string="Record Type",
        required=True,
    )

    def action_convert(self):
        self.ensure_one()
        partners = self.env["res.partner"].browse(
            self.env.context.get("active_ids", [])
        )
        for partner in partners:
            if self.fsm_record_type == "person":
                self.action_convert_person(partner)
            elif self.fsm_record_type == "location":
                self.action_convert_location(partner)
        return {"type": "ir.actions.act_window_close"}

    def _prepare_fsm_location(self, partner):
        return {"partner_id": partner.id, "owner_id": partner.id}

    def action_convert_location(self, partner):
        Location = self.env["fsm.location"]
        if Location.search_count([("partner_id", "=", partner.id)]):
            raise UserError(
                _("A Field Service Location related to that partner already exists.")
            )
        Location.create([self._prepare_fsm_location(partner)])
        partner.write({"fsm_location": True})
        self.action_other_address(partner)

    def action_convert_person(self, partner):
        Person = self.env["fsm.person"]
        if Person.search_count([("partner_id", "=", partner.id)]):
            raise UserError(
                _("A Field Service Worker related to that partner already exists.")
            )
        Person.create([{"partner_id": partner.id}])
        partner.write({"fsm_person": True})

    def action_other_address(self, partner):
        partner.child_ids.filtered(
            lambda c: c.type == "contact"
        ).write({"type": "other"})