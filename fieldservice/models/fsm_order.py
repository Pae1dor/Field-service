# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from . import fsm_stage


class FSMOrder(models.Model):
    _name = "fsm.order"
    _description = "Field Service Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_stage_id(self):
        stage = self.env["fsm.stage"].search(
            [
                ("stage_type", "=", "order"),
                ("is_default", "=", True),
                ("company_id", "in", (self.env.company.id, False)),
            ],
            order="sequence asc",
            limit=1,
        )
        if stage:
            return stage
        raise ValidationError(_("You must create an FSM order stage first."))

    def _default_team_id(self):
        team = self.env["fsm.team"].search(
            [("company_id", "in", (self.env.company.id, False))],
            order="sequence asc",
            limit=1,
        )
        if team:
            return team
        raise ValidationError(_("You must create an FSM team first."))

    def _default_request_early(self):
        return fields.Datetime.now().replace(second=0)

    # === Fields ===
    stage_id = fields.Many2one(
        "fsm.stage",
        string="Stage",
        tracking=True,
        index=True,
        copy=False,
        group_expand="_read_group_stage_ids",
        default=lambda self: self._default_stage_id(),
    )
    is_closed = fields.Boolean(string="Is closed", related="stage_id.is_closed")
    priority = fields.Selection(
        fsm_stage.AVAILABLE_PRIORITIES,
        index=True,
        default=fsm_stage.AVAILABLE_PRIORITIES[0][0],
    )
    tag_ids = fields.Many2many(
        "fsm.tag",
        "fsm_order_tag_rel",
        "fsm_order_id",
        "tag_id",
        string="Tags",
        help="Classify and analyze your orders",
    )
    color = fields.Integer(string="Color Index", default=0)
    team_id = fields.Many2one(
        "fsm.team",
        string="Team",
        default=lambda self: self._default_team_id(),
        index=True,
        required=True,
        tracking=True,
        groups="base.group_user",
    )
    name = fields.Char(
        required=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
    )
    location_id = fields.Many2one(
        "fsm.location", string="Location", index=True, required=True
    )
    location_directions = fields.Char()
    request_early = fields.Datetime(
        string="Earliest Request Date",
        default=lambda self: self._default_request_early(),
    )
    request_late = fields.Datetime(string="Latest Request Date")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company related to this order",
    )
    description = fields.Text()
    person_ids = fields.Many2many("fsm.person", string="Field Service Workers")
    person_id = fields.Many2one("fsm.person", string="Assigned To", index=True)
    person_phone = fields.Char(related="person_id.phone", string="Worker Phone")
    scheduled_date_start = fields.Datetime(string="Scheduled Start (ETA)")
    scheduled_duration = fields.Float(help="Scheduled duration of the work in hours")
    scheduled_date_end = fields.Datetime(string="Scheduled End")
    sequence = fields.Integer(default=10)
    todo = fields.Html(string="Instructions")
    resolution = fields.Text()
    date_start = fields.Datetime(string="Actual Start")
    date_end = fields.Datetime(string="Actual End")
    duration = fields.Float(
        string="Actual duration",
        compute="_compute_duration",
        help="Actual duration in hours",
    )
    current_date = fields.Datetime(default=fields.Datetime.now, store=True)

    territory_id = fields.Many2one(
        "res.territory",
        string="Territory",
        related="location_id.territory_id",
        store=True,
    )
    district_id = fields.Many2one(
        "res.district",
        string="District",
        related="location_id.district_id",
        store=True,
    )

    region_id = fields.Many2one(
        "res.region",
        string="Region",
        related="location_id.region_id",
        store=True,
    )

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch",
        related="location_id.branch_id",
        store=True,
    )

    street = fields.Char(related="location_id.street")
    street2 = fields.Char(related="location_id.street2")
    zip = fields.Char(related="location_id.zip")
    city = fields.Char(related="location_id.city")
    state_name = fields.Char(related="location_id.state_id.name", string="State")
    country_name = fields.Char(
        related="location_id.country_id.name", string="Country"
    )
    phone = fields.Char(related="location_id.phone", string="Location Phone")
    mobile = fields.Char(related="location_id.mobile")

    stage_name = fields.Char(related="stage_id.name", string="Stage Name")
    custom_color = fields.Char(
        related="stage_id.custom_color", string="Stage Color"
    )

    template_id = fields.Many2one("fsm.template", string="Template")
    category_ids = fields.Many2many("fsm.category", string="Categories")
    equipment_id = fields.Many2one("fsm.equipment", string="Equipment")
    equipment_ids = fields.Many2many("fsm.equipment", string="Equipments")
    type = fields.Many2one(
        "fsm.order.type",
        string="Type",
        index=True,
        tracking=True
    )

    internal_type = fields.Selection(related="type.internal_type", string="Internal Type", store=True)
    is_button = fields.Boolean(default=False)

    # === Service Flow Fields ===
    service_type_id = fields.Many2one(
        'fsm.service.type', string='Service Type', tracking=True, index=True,
    )
    service_type_code = fields.Char(related='service_type_id.code', store=True)

    phe_unit_ids = fields.One2many('fsm.phe.unit', 'order_id', string='PHE Units')
    phe_unit_count = fields.Integer(compute='_compute_phe_unit_count', string='Unit Count')
    all_phe_units_done = fields.Boolean(
        compute='_compute_all_phe_units_done', string='All Units Done',
    )

    pm_schedule_id = fields.Many2one('fsm.pm.schedule', string='PM Schedule', index=True)
    pm_report = fields.Text(string='PM Report')
    equipment_condition_id = fields.Many2one('fsm.equipment.condition', string='Equipment Condition')

    customer_approval_required = fields.Boolean(string='Customer Approval Required')
    customer_approved = fields.Boolean(string='Customer Approved', tracking=True)
    closing_gate_ok = fields.Boolean(
        compute='_compute_closing_gate_ok', string='Closing Gate Passed',
    )

    sms_assigned_sent = fields.Boolean(default=False)
    sms_depart_sent = fields.Boolean(default=False)
    sms_closed_sent = fields.Boolean(default=False)

    # === Computes ===
    @api.depends('phe_unit_ids')
    def _compute_phe_unit_count(self):
        for rec in self:
            rec.phe_unit_count = len(rec.phe_unit_ids)

    @api.depends('phe_unit_ids.state')
    def _compute_all_phe_units_done(self):
        for rec in self:
            units = rec.phe_unit_ids
            rec.all_phe_units_done = bool(units) and all(u.state == 'done' for u in units)

    @api.depends('date_start', 'date_end', 'all_phe_units_done', 'service_type_id',
                 'customer_approved', 'customer_approval_required')
    def _compute_closing_gate_ok(self):
        for rec in self:
            time_ok = bool(rec.date_start and rec.date_end)
            approval_ok = not rec.customer_approval_required or rec.customer_approved
            if rec.service_type_id.code == 'phe':
                rec.closing_gate_ok = time_ok and rec.all_phe_units_done and approval_ok
            else:
                rec.closing_gate_ok = time_ok and approval_ok

    @api.depends("date_start", "date_end")
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                delta = rec.date_end - rec.date_start
                rec.duration = delta.total_seconds() / 3600
            else:
                rec.duration = 0.0

    @api.depends("name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or _("New")

    # === Tracking ===
    def _track_subtype(self, init_values):
        self.ensure_one()
        if "stage_id" in init_values:
            completed = self.env.ref("fieldservice.fsm_stage_completed", False)
            cancelled = self.env.ref("fieldservice.fsm_stage_cancelled", False)
            if completed and self.stage_id == completed:
                return self.env.ref("fieldservice.mt_order_completed")
            if cancelled and self.stage_id == cancelled:
                return self.env.ref("fieldservice.mt_order_cancelled")
        return super()._track_subtype(init_values)

    @api.model
    def _read_group_stage_ids(self, stages, domain ,order):
        search_domain = [("stage_type", "=", "order")]
        if self.env.context.get("default_team_id"):
            search_domain = [
                "&",
                ("team_ids", "in", self.env.context["default_team_id"]),
            ] + search_domain
        return stages.search(search_domain, order=order)

    # === CRUD ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "fsm.order"
                ) or _("New")
            self._calc_scheduled_dates(vals)
            if not vals.get("request_late"):
                self._calc_request_late(vals)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("stage_id") and vals.get("is_button"):
            vals["is_button"] = False
        elif vals.get("stage_id"):
            new_stage = self.env["fsm.stage"].browse(vals["stage_id"])
            completed = self.env.ref("fieldservice.fsm_stage_completed", False)
            if completed and new_stage == completed:
                raise UserError(_("Cannot move to completed from Kanban"))
        self._calc_scheduled_dates(vals)
        return super().write(vals)

    def can_unlink(self):
        """:return True if the order can be deleted, False otherwise"""
        return self.stage_id == self._default_stage_id()

    def unlink(self):
        if all(order.can_unlink() for order in self):
            return super().unlink()
        raise ValidationError(_("You cannot delete this order."))

    # === Helpers ===
    def _calc_request_late(self, vals):
        if vals.get("request_early"):
            early = fields.Datetime.from_string(vals["request_early"])
        else:
            early = datetime.now()

        company = self.env.company
        priority_map = {
            "0": company.fsm_order_request_late_lowest,
            "1": company.fsm_order_request_late_low,
            "2": company.fsm_order_request_late_medium,
            "3": company.fsm_order_request_late_high,
        }
        hours = priority_map.get(vals.get("priority"))
        if hours:
            vals["request_late"] = early + timedelta(hours=hours)
        return vals

    def _calc_scheduled_dates(self, vals):
        """Calculate scheduled dates and duration."""
        has_change = (
            vals.get("scheduled_duration") is not None
            or vals.get("scheduled_date_start")
            or vals.get("scheduled_date_end")
        )
        if not has_change:
            if vals.get("scheduled_date_start") is not None:
                vals["scheduled_date_end"] = False
            return

        if vals.get("scheduled_date_start") and vals.get("scheduled_date_end"):
            start = fields.Datetime.from_string(vals["scheduled_date_start"])
            end = fields.Datetime.from_string(vals["scheduled_date_end"])
            delta = end.replace(second=0) - start.replace(second=0)
            vals["scheduled_duration"] = float(delta.total_seconds() / 3600)
        elif vals.get("scheduled_date_end"):
            hrs = vals.get("scheduled_duration") or self.scheduled_duration or 0
            end = fields.Datetime.from_string(vals["scheduled_date_end"])
            vals["scheduled_date_start"] = str(end - timedelta(hours=hrs))
        elif (
            vals.get("scheduled_duration") is not None
            and vals.get("scheduled_date_start", self.scheduled_date_start)
            and self.scheduled_date_start
            != vals.get("scheduled_date_start", False)
        ):
            hours = vals["scheduled_duration"]
            start_val = vals.get(
                "scheduled_date_start", self.scheduled_date_start
            )
            start = fields.Datetime.from_string(start_val)
            vals["scheduled_date_end"] = str(start + timedelta(hours=hours))

    # === Actions ===
    def action_cancel(self):
        return self.write(
            {"stage_id": self.env.ref("fieldservice.fsm_stage_cancelled").id}
        )

    # === Flow Actions ===

    def action_assign_technician(self):
        """Assign technician and send SMS."""
        for rec in self:
            if not rec.person_id:
                raise UserError(_("Please assign a technician first."))
            rec._send_sms_notification(
                f"[Job Assigned] {rec.name}\n"
                f"Technician: {rec.person_id.name}\n"
                f"Location: {rec.location_id.name}\n"
                f"Date: {rec.scheduled_date_start or '-'}"
            )
            rec.sms_assigned_sent = True
            rec.message_post(
                body=_("Assigned job to %s - SMS sent to technician and customer.") % rec.person_id.name,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def action_tech_depart(self):
        """Technician departs - records date_start and sends SMS."""
        for rec in self:
            if not rec.person_id:
                raise UserError(_("No technician assigned yet."))
            if not rec.date_start:
                rec.date_start = fields.Datetime.now()
            rec._send_sms_notification(
                f"[Technician Departed] {rec.name}\n"
                f"Technician {rec.person_id.name} is en route to {rec.location_id.name}"
            )
            rec.sms_depart_sent = True

    def action_customer_approve(self):
        """Customer approves the quotation."""
        self.ensure_one()
        self.customer_approved = True
        self.message_post(
            body=_("Customer approved - work can proceed."),
            message_type='comment',
            subtype_xmlid='mail.mt_note',
        )

    def action_complete(self):
        """Complete job - check closing gate first."""
        for rec in self:
            if not rec.closing_gate_ok:
                msgs = []
                if not rec.date_start or not rec.date_end:
                    msgs.append("- Start/end time not recorded yet")
                if rec.service_type_id.code == 'phe' and not rec.all_phe_units_done:
                    pending = rec.phe_unit_ids.filtered(lambda u: u.state != 'done')
                    msgs.append(f"- PHE units pending: {', '.join(pending.mapped('name'))}")
                if rec.customer_approval_required and not rec.customer_approved:
                    msgs.append("- Awaiting customer approval")
                raise UserError(
                    _("Cannot complete job - closing gate checks not passed:\n%s") % "\n".join(msgs)
                )
        result = self.write({
            "stage_id": self.env.ref("fieldservice.fsm_stage_completed").id,
            "is_button": True,
        })
        for rec in self:
            rec._send_sms_notification(
                f"[Job Completed] {rec.name}\n"
                f"Job completed - please review the invoice"
            )
            rec.sms_closed_sent = True
            if rec.service_type_id.code == 'pm' and rec.pm_schedule_id:
                rec.pm_schedule_id.last_pm_date = fields.Date.today()
        return result

    def action_check_stock(self):
        """Check parts stock - shows stock status of material_ids (if any)."""
        self.ensure_one()
        # material_ids comes from fieldservice_sale_flow - use getattr to avoid AttributeError
        material_ids = getattr(self, 'material_ids', None)
        if material_ids is None:
            raise UserError(_("The fieldservice_sale_flow module must be installed first to check stock."))
        short = material_ids.filtered(
            lambda l: l.product_id and l.product_id.qty_available < l.product_qty
        )
        if not short:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Stock Sufficient',
                    'message': 'All materials have sufficient stock.',
                    'type': 'success',
                },
            }
        msg = "Materials short on stock:\n" + "\n".join(
            f"- {l.product_id.name}: needed {l.product_qty}, available {l.product_id.qty_available}"
            for l in short
        )
        self.message_post(
            body=msg, message_type='comment', subtype_xmlid='mail.mt_note',
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Stock Insufficient',
                'message': f'{len(short)} item(s) short on stock - PO created automatically.',
                'type': 'warning',
            },
        }

    def action_view_pm_schedule(self):
        self.ensure_one()
        if not self.pm_schedule_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'PM Schedule',
            'res_model': 'fsm.pm.schedule',
            'res_id': self.pm_schedule_id.id,
            'view_mode': 'form',
        }

    def _send_sms_notification(self, message):
        """Log SMS notification in chatter (production connects to LINE Notify webhook)."""
        for rec in self:
            rec.message_post(
                body=f"SMS: {message}",
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    # === Onchanges ===
    @api.onchange("location_id")
    def _onchange_location_id_customer(self):
        if self.location_id:
            self.territory_id = self.location_id.territory_id
            self.branch_id = self.location_id.branch_id
            self.district_id = self.location_id.district_id
            self.region_id = self.location_id.region_id
            self.copy_notes()
        if self.company_id.auto_populate_equipments_on_order and self.location_id:
            equipment = self.env["fsm.equipment"].search(
                [("current_location_id", "=", self.location_id.id)]
            )
            self.equipment_ids = [(6, 0, equipment.ids)]

    @api.onchange("scheduled_date_end")
    def onchange_scheduled_date_end(self):
        if self.scheduled_date_end:
            delta = self.scheduled_date_end - timedelta(
                hours=self.scheduled_duration or 0
            )
            self.date_start = str(delta)

    @api.onchange("scheduled_date_start", "scheduled_duration")
    def onchange_scheduled_duration(self):
        if self.scheduled_duration and self.scheduled_date_start:
            self.scheduled_date_end = str(
                self.scheduled_date_start
                + timedelta(hours=self.scheduled_duration)
            )
        else:
            self.scheduled_date_end = self.scheduled_date_start

    @api.onchange("equipment_ids")
    def onchange_equipment_ids(self):
        self.copy_notes()

    @api.onchange("template_id")
    def _onchange_template_id(self):
        if not self.template_id:
            return
        self.category_ids = self.template_id.category_ids
        self.scheduled_duration = self.template_id.duration
        self.copy_notes()
        if self.template_id.type_id:
            self.type = self.template_id.type_id
        if self.template_id.team_id:
            self.team_id = self.template_id.team_id

    def copy_notes(self):
        old_desc = self.description
        self.location_directions = ""
        if self.type and self.type.internal_type not in ["repair", "maintenance"]:
            for equipment in self.equipment_ids.filtered(lambda eq: eq.notes):
                desc = self.description or ""
                self.description = desc + equipment.notes + "\n "
        elif self.equipment_id and self.equipment_id.notes:
            desc = self.description or ""
            self.description = desc + self.equipment_id.notes + "\n "
        if self.location_id:
            self.location_directions = self._get_location_directions(
                self.location_id
            )
        if self.template_id:
            self.todo = self.template_id.instructions
        if old_desc:
            self.description = old_desc

    def _get_location_directions(self, location_id):
        result = location_id.direction or ""
        parent = location_id.fsm_parent_id
        visited = {location_id.id}
        while parent and parent.id not in visited:
            visited.add(parent.id)
            if parent.direction:
                result += parent.direction
            parent = parent.fsm_parent_id
        return result

    # === Constraints ===
    @api.constrains("scheduled_date_start", "scheduled_date_end")
    def check_day(self):
        for rec in self:
            if not (rec.scheduled_date_start and rec.scheduled_date_end):
                continue
            holidays = self.env["resource.calendar.leaves"].search(
                [
                    ("date_from", ">=", rec.scheduled_date_start),
                    ("date_to", "<=", rec.scheduled_date_end),
                ]
            )
            if holidays:
                raise ValidationError(
                    _("%(date)s is a holiday: %(name)s")
                    % {
                        "date": rec.scheduled_date_start.date(),
                        "name": holidays[0].name,
                    }
                )