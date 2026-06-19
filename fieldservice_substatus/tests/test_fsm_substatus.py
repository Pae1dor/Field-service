# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class FSMSubstatusCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.WorkOrder = cls.env["fsm.order"]
        cls.stage_id = cls.WorkOrder._default_stage_id()
        cls.init_values = {"sub_stage_id": cls.stage_id.sub_stage_id.id}
        cls.StageStatus = cls.env["fsm.stage.status"]

        # create a Res Partner to be converted to FSM Location/Person
        cls.test_loc_partner = cls.env["res.partner"].create(
            {"name": "Test Loc Partner", "phone": "ABC", "email": "tlp@email.com"}
        )
        # create expected FSM Location to compare to converted FSM Location
        cls.test_location = cls.env["fsm.location"].create(
            {
                "name": "Test Location",
                "phone": "123",
                "email": "tp@email.com",
                "partner_id": cls.test_loc_partner.id,
                "owner_id": cls.test_loc_partner.id,
            }
        )
        cls.stage = cls.env["fsm.stage"].create(
            {
                "name": "Stage 1",
                "sequence": 2,
                "stage_type": "order",
                "sub_stage_id": cls.stage_id.sub_stage_id.id,
            }
        )

    def test_fsm_orders(self):
        """Test creating new workorders, and test following functions."""
        # Create an Orders
        hours_diff = 100
        date_start = fields.Datetime.today()

        order = self.WorkOrder.create(
            {
                "location_id": self.test_location.id,
                "date_start": date_start,
                "date_end": date_start + timedelta(hours=hours_diff),
                "request_early": fields.Datetime.today(),
            }
        )

        order._track_subtype(self.init_values)
        order._track_subtype({})
        self.stage.onchange_sub_stage_id()

        stage_status_id = self.StageStatus.with_context(
            fsm_order_stage_id=self.stage_id.id
        ).create({"name": "Test"})

        stage_status_id.search([])

        order.stage_id = self.stage.id