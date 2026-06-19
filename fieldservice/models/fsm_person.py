# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMPerson(models.Model):
    _name = "fsm.person"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread.blacklist", "fsm.model.mixin"]
    _description = "Field Service Worker"
    _stage_type = "worker"

    partner_id = fields.Many2one(
        "res.partner",
        string="Related Partner",
        required=True,
        ondelete="restrict",
        delegate=True,
        auto_join=True,
    )
    category_ids = fields.Many2many("fsm.category", string="Categories")
    calendar_id = fields.Many2one("resource.calendar", string="Working Schedule")
    territory_ids = fields.Many2many("res.territory", string="Territories")
    active = fields.Boolean(default=True)
    active_partner = fields.Boolean(
        related="partner_id.active", readonly=True, string="Partner is Active"
    )

    def toggle_active(self):
        # Reactivate partner first if both archived
        for person in self:
            if not person.active and not person.partner_id.active:
                person.partner_id.with_context(
                    no_fsm_toggle=True
                ).toggle_active()
        return super().toggle_active()

    @api.model
    def _search(
        self,
        domain,
        offset=0,
        limit=None,
        order=None,
        access_rights_uid=None,
    ):
        # Translate location_ids domain into person_id list via ORM (safe)
        new_domain = []
        for arg in domain:
            if (
                isinstance(arg, (list, tuple))
                and len(arg) == 3
                and arg[0] == "location_ids"
            ):
                value = arg[2]
                if isinstance(value, int):
                    location_ids = [value]
                elif isinstance(value, str):
                    locations = self.env["fsm.location"].search(
                        [("complete_name", "ilike", value)]
                    )
                    location_ids = locations.ids
                else:
                    location_ids = list(value) if value else []

                if location_ids:
                    junction = self.env["fsm.location.person"].search(
                        [("location_id", "in", location_ids)]
                    )
                    new_domain.append(("id", "in", junction.mapped("person_id").ids))
                else:
                    new_domain.append(("id", "=", False))
            else:
                new_domain.append(arg)

        return super()._search(
            new_domain,
            offset=offset,
            limit=limit,
            order=order,
            access_rights_uid=access_rights_uid,
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["fsm_person"] = True
        return super().create(vals_list)