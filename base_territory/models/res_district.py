# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResDistrict(models.Model):
    _name = "res.district"
    _description = "District"
    name = fields.Char(required=True)
    name_en = fields.Char(string="English Name")  # เติมบรรทัดนี้เข้าไป
    region_id = fields.Many2one("res.region", string="Region")
    state_id = fields.Many2one('res.country.state', string='Province')  # <-- ต้องมีบรรทัดนี้ชื่อนี้เป๊ะๆ!
    partner_id = fields.Many2one("res.partner", string="District Manager")
    description = fields.Char()
