{
    "name": "l10n Location Base",
    "version": "17.0.1.0.0",
    "author": "IoT Innovation co.,ltd.",
    "website": "https://www.iot-innovation.co.th/",
    "category": "Localization (TH) / Contacts",
    "license": "LGPL-3",
    "icon": "/company_assets/static/description/icon.png",
    "depends": [
        "base",
        "company_assets",
        "contacts",
        "l10n_th_partner_name",
        "hr"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/res_district_views.xml",
        "views/res_subdistrict_views.xml",
        "views/res_partner_list_views.xml",
        "views/hr_employee_views.xml",
        "data/res.district.csv",
        "data/res.subdistrict.csv"
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_th_location_base/static/src/css/contact_configurator.css"
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False
}
