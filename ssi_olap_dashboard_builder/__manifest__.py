{
    "name": "OLAP Dashboard Builder",
    "version": "14.0.1.0.0",
    "summary": "Buat dashboard analitik ClickHouse langsung dari Odoo, tanpa coding",
    "description": """
Dashboard Builder untuk OLAP Platform
======================================
Buat, validasi, dan publish custom report ClickHouse dari Odoo. Report yang
dipublish otomatis tampil di section "Custom Reports" pada Go dashboard.
""",
    "category": "Reporting",
    "author": "mikevhe18",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/olap_dashboard_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
}
