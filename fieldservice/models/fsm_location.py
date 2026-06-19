# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class FSMLocation(models.Model):
    _name = "fsm.location"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread", "mail.activity.mixin", "fsm.model.mixin"]
    _description = "Field Service Location"
    _stage_type = "location"

    direction = fields.Char()
    partner_id = fields.Many2one(
        "res.partner",
        string="Related Partner",
        required=True,
        ondelete="restrict",
        delegate=True,
        auto_join=True,
    )
    owner_id = fields.Many2one(
        "res.partner",
        string="Related Owner",
        required=True,
        ondelete="restrict",
        auto_join=True,
    )
    contact_id = fields.Many2one(
        "res.partner",
        string="Primary Contact",
        domain="[('is_company', '=', False), ('fsm_location', '=', False)]",
        index=True,
    )
    description = fields.Char()
    territory_id = fields.Many2one("res.territory", string="Territory")
    branch_id = fields.Many2one("res.branch", string="Branch")
    district_id = fields.Many2one("res.district", string="District")
    region_id = fields.Many2one("res.region", string="Region")
    territory_manager_id = fields.Many2one(
        string="Primary Assignment", related="territory_id.person_id"
    )
    district_manager_id = fields.Many2one(
        string="District Manager", related="district_id.partner_id"
    )
    region_manager_id = fields.Many2one(
        string="Region Manager", related="region_id.partner_id"
    )
    branch_manager_id = fields.Many2one(
        string="Branch Manager", related="branch_id.partner_id"
    )

    calendar_id = fields.Many2one("resource.calendar", string="Office Hours")
    fsm_parent_id = fields.Many2one("fsm.location", string="Parent", index=True)
    notes = fields.Text(string="Location Notes")
    person_ids = fields.One2many(
        "fsm.location.person", "location_id", string="Workers"
    )
    contact_count = fields.Integer(
        string="Contacts Count", compute="_compute_contact_ids"
    )
    equipment_count = fields.Integer(
        string="Equipment", compute="_compute_equipment_ids"
    )
    sublocation_count = fields.Integer(
        string="Sub Locations", compute="_compute_sublocation_ids"
    )
    complete_name = fields.Char(
        compute="_compute_complete_name", recursive=True, store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["fsm_location"] = True
        return super().create(vals_list)

    @api.depends("partner_id.name", "fsm_parent_id.complete_name", "ref")
    def _compute_complete_name(self):
        for loc in self:
            parts = []
            if loc.fsm_parent_id:
                parts.append(loc.fsm_parent_id.complete_name)

            name = loc.partner_id.name if loc.partner_id else ""
            if loc.ref:
                parts.append(f"[{loc.ref}] {name}")
            else:
                parts.append(name or "")
            loc.complete_name = " / ".join(p for p in parts if p)

    @api.depends("complete_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.complete_name or ""

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        domain = domain or []
        if name:
            field = (
                "complete_name"
                if self.env.company.search_on_complete_name
                else "name"
            )
            name_domain = expression.OR([
                [("ref", "ilike", name)],
                [(field, operator, name)]
            ])
            domain = expression.AND([name_domain, domain])
        return self._search(domain, limit=limit, order=order)

    @api.onchange("fsm_parent_id")
    def _onchange_fsm_parent_id(self):
        if not self.fsm_parent_id:
            return
        parent = self.fsm_parent_id
        self.owner_id = parent.owner_id
        self.contact_id = parent.contact_id
        self.direction = parent.direction
        self.street = parent.street
        self.street2 = parent.street2
        self.city = parent.city
        self.zip = parent.zip
        self.state_id = parent.state_id
        self.country_id = parent.country_id
        self.tz = parent.tz
        self.territory_id = parent.territory_id

    @api.onchange("territory_id")
    def _onchange_territory_id(self):
        if not self.territory_id:
            return
        self.branch_id = self.territory_id.branch_id
        if self.env.company.auto_populate_persons_on_location:
            person_vals_list = [
                (0, 0, {"person_id": person.id, "sequence": 10})
                for person in self.territory_id.person_ids
            ]
            self.person_ids = person_vals_list or False

    @api.onchange("branch_id")
    def _onchange_branch_id(self):
        if not self.branch_id:
            return
        self.branch_manager_id = self.branch_id.partner_id
        self.district_id = self.branch_id.district_id

    @api.onchange("district_id")
    def _onchange_district_id(self):
        if not self.district_id:
            return
        self.district_manager_id = self.district_id.partner_id
        self.region_id = self.district_id.region_id

    @api.onchange("region_id")
    def _onchange_region_id(self):
        if not self.region_id:
            return
        self.region_manager_id = self.region_id.partner_id

    def _get_descendant_locations(self):
        """Return self + all descendant locations (recursive)."""
        self.ensure_one()
        result = self
        children = self.search([("fsm_parent_id", "=", self.id)])
        for child in children:
            result |= child._get_descendant_locations()
        return result

    def _count_related(self, model_name, field_name):
        """Count related records across self + descendants."""
        self.ensure_one()
        all_locs = self._get_descendant_locations()
        return self.env[model_name].search_count(
            [(field_name, "in", all_locs.ids)]
        )

    def _get_related(self, model_name, field_name):
        """Get related recordset across self + descendants."""
        self.ensure_one()
        all_locs = self._get_descendant_locations()
        return self.env[model_name].search([(field_name, "in", all_locs.ids)])

    def _compute_contact_ids(self):
        for loc in self:
            loc.contact_count = loc._count_related(
                "res.partner", "service_location_id"
            )

    def _compute_equipment_ids(self):
        for loc in self:
            loc.equipment_count = loc._count_related(
                "fsm.equipment", "location_id"
            )

    def _compute_sublocation_ids(self):
        for loc in self:
            loc.sublocation_count = self.search_count(
                [("fsm_parent_id", "child_of", loc.id)]
            )

    def action_view_contacts(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "contacts.action_contacts"
        )
        contacts = self._get_related("res.partner", "service_location_id")
        action["context"] = {
            **self.env.context,
            "group_by": "",
            "default_service_location_id": self.id,
        }
        if len(contacts) == 1:
            action["views"] = [
                (self.env.ref("base.view_partner_form").id, "form")
            ]
            action["res_id"] = contacts.id
        else:
            action["domain"] = [("id", "in", contacts.ids)]
        return action

    def action_view_equipment(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "fieldservice.action_fsm_equipment"
        )
        equipment = self._get_related("fsm.equipment", "location_id")
        action["context"] = {
            **self.env.context,
            "group_by": "",
            "default_location_id": self.id,
        }
        if len(equipment) == 1:
            action["views"] = [
                (self.env.ref("fieldservice.fsm_equipment_form_view").id, "form")
            ]
            action["res_id"] = equipment.id
        else:
            action["domain"] = [("id", "in", equipment.ids)]
        return action

    def action_view_sublocation(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "fieldservice.action_fsm_location"
        )
        sublocations = self.search([("fsm_parent_id", "child_of", self.id)])
        sublocations -= self
        action["context"] = {
            **self.env.context,
            "group_by": "",
            "default_fsm_parent_id": self.id,
        }
        if len(sublocations) == 1:
            action["views"] = [
                (self.env.ref("fieldservice.fsm_location_form_view").id, "form")
            ]
            action["res_id"] = sublocations.id
        else:
            action["domain"] = [("id", "in", sublocations.ids)]
        return action

    def geo_localize(self):
        return self.partner_id.geo_localize()

    @api.constrains("fsm_parent_id")
    def _check_location_recursion(self):
        if not self._check_recursion(parent="fsm_parent_id"):
            raise ValidationError(_("You cannot create recursive location."))
        return True

    @api.onchange("country_id")
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange("state_id")
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id


class FSMPerson(models.Model):
    _inherit = "fsm.person"

    location_ids = fields.One2many(
        "fsm.location.person", "person_id", string="Linked Locations"
    )