from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    # Exist Fields in Work Address
        # private_street
        # private_street2
        # private_city
        # private_zip
        # country_id 
        # private_state_id

    # Address fields in hr.employee model
    private_house_no = fields.Char(string="House No", required=False)
    private_moo = fields.Char(string="Moo", required=False)
    private_villa = fields.Char(string="Villa", required=False)
    private_alley = fields.Char(string="Alley", required=False)
    private_sub_alley = fields.Char(string="Sub", required=False)
    private_street_new = fields.Char(string="Street", required=False)
    
    private_building = fields.Char(string="Building", required=False)
    private_floor = fields.Char(string="Floor", required=False)
    private_room_no = fields.Char(string="Room No", required=False)
    
    private_district_id = fields.Many2one('res.district', string="District")
    private_subdistrict_id = fields.Many2one('res.subdistrict', string="Sub District")
    private_country_id = fields.Many2one('res.country', string="Country", default=217)
    private_zip = fields.Char(string='ZIP', related='private_subdistrict_id.zip_code', store=True, readonly=True)
    
    # กำหนดฟิลด์มาตรฐานให้คำนวณอัตโนมัติ
    private_street = fields.Char(compute='_compute_address_fields', store=True, readonly=False)
    private_street2 = fields.Char(compute='_compute_address_fields', store=True, readonly=False)
    private_city = fields.Char(compute='_compute_address_fields', store=True, readonly=False)
    
    @api.depends('private_house_no', 'private_moo', 'private_villa', 'private_alley', 'private_sub_alley', 'private_street_new', 'private_building', 'private_floor', 'private_room_no', 'private_district_id', 'private_subdistrict_id', 'private_state_id', 'private_country_id')
    def _compute_address_fields(self):
        for partner in self:
            # กลุ่มที่ 1: อาคาร, ชั้น, ห้อง, หมู่
            addr_parts1 = []
            if partner.private_building:
                addr_parts1.append(f"อาคาร {partner.private_building}")
            if partner.private_floor:
                addr_parts1.append(f"ชั้น {partner.private_floor}")
            if partner.private_room_no:
                addr_parts1.append(f"ห้อง {partner.private_room_no}")
            if partner.private_moo:
                addr_parts1.append(f"หมู่ที่ {partner.private_moo}")
                
            # กลุ่มที่ 2: เลขที่, หมู่บ้าน, ซอย, street_new, แยก
            addr_parts2 = []
            if partner.private_house_no:
                addr_parts2.append(f"เลขที่ {partner.private_house_no}")
            if partner.private_villa:
                addr_parts2.append(f"หมู่บ้าน {partner.private_villa}")
            if partner.private_alley:
                addr_parts2.append(f"ซอย {partner.private_alley}")
            if partner.private_street_new:
                addr_parts2.append(f"ถนน {partner.private_street_new}")
            if partner.private_sub_alley:
                addr_parts2.append(f"แยก {partner.private_sub_alley}")
            
            # กำหนดค่าให้ฟิลด์มาตรฐานของ Odoo
            partner.private_street = " ".join(addr_parts1) if addr_parts1 else False
            partner.private_street2 = " ".join(addr_parts2) if addr_parts2 else False
            
            # ตำบล/อำเภอ ใส่ในฟิลด์ city
            subdistrict_name = partner.private_subdistrict_id.name if partner.private_subdistrict_id else ""
            district_name = partner.private_district_id.name if partner.private_district_id else ""
            
            city_parts = []
            if subdistrict_name:
                city_parts.append(f"ตำบล/แขวง {subdistrict_name}")
            if district_name:
                city_parts.append(f"อำเภอ/เขต {district_name}")
            
            partner.private_city = " ".join(city_parts) if city_parts else False

    @api.onchange('private_subdistrict_id')
    def _onchange_subdistrict_id(self):
        """Update zip code when subdistrict changes"""
        if self.private_subdistrict_id:
            self.private_zip = self.private_subdistrict_id.zip_code
        else:
            self.private_zip = False

    @api.onchange('private_country_id')
    def _onchange_country_id(self):
        if self.private_country_id:
            self.private_state_id = False
            self.private_district_id = False
            self.private_subdistrict_id = False
            self.private_zip = False 
            
    @api.onchange('private_state_id')
    def _onchange_state_id(self):
        if self.private_state_id:
            self.private_district_id = False
            self.private_subdistrict_id = False
            self.private_zip = False 
            
    @api.onchange('private_district_id')
    def _onchange_district_id(self):
        if self.private_district_id:
            self.private_subdistrict_id = False
            self.private_zip = False