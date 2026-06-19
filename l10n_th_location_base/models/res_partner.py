#ms_res_partner.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
# Province
# models/res_province.py
class ResProvince(models.Model):
    _name = 'res.province'
    _description = 'Province'
    province_id = fields.Integer(string="Province ID", required=True)
    name = fields.Char(string="Province TH", required=True)
    province_en = fields.Char(string="Province EN", required=True)

# District model
class District(models.Model):
    _name = 'res.district'
    _description = 'District'
    
    name = fields.Char(string='District Name', required=True)
    name_en = fields.Char(string='District Name (EN)', required=False)
    code = fields.Char(string='District Code', required=False)
    dist_id = fields.Integer(string='District Id')
    state_id = fields.Many2one('res.province', string='Province', required=True)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to support multi-language search"""
        if args is None:
            args = []
        
        # Get user's language
        lang = self.env.context.get('lang', 'th_TH')
        
        # Search in appropriate language field
        if lang == 'en_US':
            # Search in English name if available, otherwise use default name
            domain = args + ['|', ('name_en', operator, name), ('name', operator, name)]
        else:
            # Search in Thai name (default name field)
            domain = args + [('name', operator, name)]
            
        districts = self.search(domain, limit=limit)
        return districts.name_get()
    
    def name_get(self):
        """Override name_get to display name in user's language"""
        result = []
        lang = self.env.context.get('lang', 'th_TH')
        
        for district in self:
            if lang == 'en_US' and district.name_en:
                name = district.name_en
            else:
                name = district.name
            result.append((district.id, name))
        return result
    
# Sub-district model
class SubDistrict(models.Model):
    _name = 'res.subdistrict'
    _description = 'Sub District'

    subdist_id = fields.Integer(string='Sub District ID')
    name = fields.Char(string='Sub District Name', required=True)
    name_en = fields.Char(string='Sub District Name (EN)', required=False)
    code = fields.Integer(string='Sub District Code', required=False)
    district_id = fields.Many2one('res.district', string='อำเภอ')
    district_en_name = fields.Char(related='district_id.name_en', string="District Name (EN)", readonly=True)
    zip_code = fields.Char(string='Zip Code')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to support multi-language search"""
        if args is None:
            args = []
        
        lang = self.env.context.get('lang', 'th_TH')
        
        if lang == 'en_US':
            domain = args + ['|', ('name_en', operator, name), ('name', operator, name)]
        else:
            domain = args + [('name', operator, name)]
            
        subdistricts = self.search(domain, limit=limit)
        return subdistricts.name_get()
    
    def name_get(self):
        """Override name_get to display name in user's language"""
        result = []
        lang = self.env.context.get('lang', 'th_TH')
        
        for subdistrict in self:
            if lang == 'en_US' and subdistrict.name_en:
                name = subdistrict.name_en
            else:
                name = subdistrict.name
            result.append((subdistrict.id, name))
        return result
    
# Province model
class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    name = fields.Char()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to support multi-language search"""
        if args is None:
            args = []
        
        lang = self.env.context.get('lang', 'th_TH')
        
        if lang == 'en_US':
            domain = args + ['|', ('name_en', operator, name), ('name', operator, name)]
        else:
            domain = args + [('name', operator, name)]
            
        states = self.search(domain, limit=limit)
        return states.name_get()
    
    def name_get(self):
        """Override name_get to display name in user's language"""
        result = []
        lang = self.env.context.get('lang', 'th_TH')
        
        for state in self:
            if lang == 'en_US' and state.name_en:
                name = state.name_en
            else:
                name = state.name
            result.append((state.id, name))
        return result
    
# Contacts model
class ResPartner(models.Model):
    _inherit = "res.partner"

    # เพิ่ม field ใหม่
    branch = fields.Char(string="รหัส สาขา")
    cust_no = fields.Char(string="รหัสลูกค้า")


    # Address fields in res.partner model
    house_no = fields.Char(string="เลขที่บ้าน", required=False) # House number (เลขที่บ้าน)
    moo = fields.Char(string="หมู่ที่", required=False) # Village No. (หมู่ที่)
    villa = fields.Char(string="ชื่อหมู่บ้าน", required=False) # Village name (ชื่อหมู่บ้าน)
    alley = fields.Char(string="ซอย", required=False) # Alley/Soi (ซอย)
    sub_alley = fields.Char(string="แยก", required=False) # Sub-alley (แยก)
    street_new = fields.Char(string="ถนน", required=False) # Street - New field (ถนน)
    building = fields.Char(string="อาคาร", required=False) # Building (อาคาร)
    floor = fields.Char(string="ชั้น", required=False) # Floor (ชั้น)
    room_no = fields.Char(string="เลขที่ห้อง", required=False) # Room Number (เลขที่ห้อง)

    house_no_en = fields.Char(string="House No", required=False) # House number (เลขที่บ้าน)
    moo_en = fields.Char(string="Moo", required=False) # Village No. (หมู่ที่)
    villa_en = fields.Char(string="Villa", required=False) # Village name (ชื่อหมู่บ้าน)
    alley_en = fields.Char(string="Alley", required=False) # Alley/Soi (ซอย)
    sub_alley_en = fields.Char(string="Sub Alley", required=False) # Sub-alley (แยก)
    street_new_en = fields.Char(string="Street", required=False) # Street - New field (ถนน)
    building_en = fields.Char(string="Building", required=False) # Building (อาคาร)
    floor_en = fields.Char(string="Floor", required=False) # Floor (ชั้น)
    room_no_en = fields.Char(string="Room No", required=False) # Room Number (เลขที่ห้อง)



    district_id = fields.Many2one(
        'res.district',
        string="District",

    ) # City District/Area (อำเภอ)
    district_en_name = fields.Char(related='district_id.name_en', string="District Name (EN)", readonly=True)

    subdistrict_id = fields.Many2one('res.subdistrict', string="Sub District") # Sub-district/Sub-area (ตำบล)
    subdistrict_en_name = fields.Char(related='subdistrict_id.name_en', string="Sub District Name (EN)", readonly=True)
    state_id_th = fields.Many2one('res.province', string="จังหวัด", required=True) # Province (จังหวัด)
    country_id = fields.Many2one('res.country', string="Country", default=217) # Default Thailand
    zip = fields.Char(string="ZIP", related='subdistrict_id.zip_code', store=True, readonly=True)
    
    # Add automatic calculation for standard fields
    street = fields.Char(compute='_compute_address_fields', store=True, readonly=False)
    street2 = fields.Char(compute='_compute_address_fields', store=True, readonly=False)
    city = fields.Char(compute='_compute_address_fields', store=True, readonly=False)



    @api.depends('house_no', 'moo', 'villa', 'alley', 'sub_alley', 'street_new', 
                 'building', 'floor', 'room_no',

                 'district_id', 'subdistrict_id',
                 'state_id', 'country_id', 'zip', 'lang' ,
                 )
    def _compute_address_fields(self):
        for partner in self:
            # Get user language or partner language
            lang = partner.lang or self.env.context.get('lang', 'th_TH')
            
            # Language-specific address formatting
            if lang == 'en_US':
                partner._compute_address_fields_en()
            else:
                partner._compute_address_fields_th()
    
    def _compute_address_fields_th(self):
        """Compute address fields in Thai format"""
        # Group 1: Building, Floor, Room, Moo
        addr_parts1 = []
        if self.building:
            addr_parts1.append("อาคาร %s" % self.building)
        if self.floor:
            addr_parts1.append("ชั้น %s" % self.floor)
        if self.room_no:
            addr_parts1.append("ห้อง %s" % self.room_no)
        if self.moo:
            addr_parts1.append("หมู่ %s" % self.moo)
            
        # Group 2: House No, Village, Alley, street_new, Sub-alley
        addr_parts2 = []
        if self.house_no:
            addr_parts2.append("เลขที่ %s" % self.house_no)
        if self.villa:
            addr_parts2.append("หมู่บ้าน %s" % self.villa)
        if self.alley:
            addr_parts2.append("ซอย %s" % self.alley)
        if self.street_new:
            addr_parts2.append("ถนน %s" % self.street_new)
        if self.sub_alley:
            addr_parts2.append("แยก %s" % self.sub_alley)
        
        # Set values to Odoo standard fields
        self.street = " ".join(addr_parts1) if addr_parts1 else False
        self.street2 = " ".join(addr_parts2) if addr_parts2 else False
        
        # Sub-district/District in city field (Thai)
        subdistrict_name = self.subdistrict_id.name if self.subdistrict_id else ""
        district_name = self.district_id.name if self.district_id else ""
        
        city_parts = []
        if subdistrict_name:
            city_parts.append("ตำบล %s" % subdistrict_name)
        if district_name:
            city_parts.append("อำเภอ %s" % district_name)
        
        self.city = " ".join(city_parts) if city_parts else False
    
    def _compute_address_fields_en(self):
        """Compute address fields in English format"""
        # Group 1: Building, Floor, Room, Moo
        addr_parts1 = []
        if self.building:
            addr_parts1.append("Building %s" % self.building)
        if self.floor:
            addr_parts1.append("Floor %s" % self.floor)
        if self.room_no:
            addr_parts1.append("Room %s" % self.room_no)
        if self.moo:
            addr_parts1.append("Moo %s" % self.moo)
            
        # Group 2: House No, Village, Alley, street_new, Sub-alley
        addr_parts2 = []
        if self.house_no:
            addr_parts2.append("No. %s" % self.house_no)
        if self.villa:
            addr_parts2.append("Village %s" % self.villa)
        if self.alley:
            addr_parts2.append("Alley %s" % self.alley)
        if self.street_new:
            addr_parts2.append("Street %s" % self.street_new)
        if self.sub_alley:
            addr_parts2.append("Sub Alley %s" % self.sub_alley)
        
        # Set values to Odoo standard fields
        self.street = " ".join(addr_parts1) if addr_parts1 else False
        self.street2 = " ".join(addr_parts2) if addr_parts2 else False
        
        # Sub-district/District in city field (English)
        subdistrict_name = (self.subdistrict_id.name_en if self.subdistrict_id.name_en 
                           else self.subdistrict_id.name_en) if self.subdistrict_id else ""
        district_name = (self.district_id.name_en if self.district_id.name_en 
                        else self.district_id.name_en) if self.district_id else ""
        
        city_parts = []
        if subdistrict_name:
            city_parts.append("Sub-district %s" % subdistrict_name)
        if district_name:
            city_parts.append("District %s" % district_name)
        
        self.city = " ".join(city_parts) if city_parts else False
    
    @api.onchange('lang')
    def _onchange_lang(self):
        """Recompute address fields when language changes"""
        self._compute_address_fields()
    
    # @api.onchange('subdistrict_id')
    # def _onchange_subdistrict_id(self):
       # """Update zip code when subdistrict changes"""
        # if self.subdistrict_id:
        #     self.zip = self.subdistrict_id.zip_code
        #     # Auto-update district based on subdistrict
        #     if self.subdistrict_id.district_id:
        #         self.district_id = self.subdistrict_id.district_id
        #         # Auto-update state based on district
        #         if self.district_id.state_id:
        #             self.state_id = self.district_id.state_id
        # else:
        #     self.zip = False
            
    @api.onchange('district_id')
    def _onchange_district_id(self):
        """Filter subdistricts based on selected district"""
        #if self.district_id:
            # Auto-update state based on district
            # if self.district_id.state_id:
            #     self.state_id = self.district_id.state_id
            
            # Return domain to filter subdistricts
        return {
            'domain': {
                'subdistrict_id': [('district_id', '=', self.district_id.id)]
            }
        }
        # else:
        #     self.subdistrict_id = False
        #     self.zip = False
        #     return {
        #         'domain': {
        #             'subdistrict_id': []
        #         }
        #     }

    @api.onchange('state_id')
    def _onchange_state_id(self):
        """Filter districts based on selected state"""
        if self.state_id:
            self.district_id = False
            self.subdistrict_id = False
            self.zip = False
            return {
                'domain': {
                    'district_id': [('state_id', '=', self.state_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'district_id': []
                }
            }
            
    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Filter states based on selected country"""
        if self.country_id:
            self.state_id = False
            self.district_id = False
            self.subdistrict_id = False
            self.zip = False 
            return {
                'domain': {
                    'state_id': [('country_id', '=', self.country_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'state_id': []
                }
            }