# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OLAP Dashboard Builder",
    "version": "14.0.1.3.0",
    "category": "Reporting",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Michael Viriyananda <viriyananda.michael@gmail.com>",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": True,
    "external_dependencies": {
        "python": ["requests"],
    },
    "depends": [
        "base",
        "web",
        "ssi_master_data_mixin",
    ],
    "data": [
        "security/ir_module_category_data.xml",
        "security/res_groups/olap_dashboard.xml",
        "security/ir_model_access/olap_dashboard.xml",
        "security/ir_model_access/olap_dashboard_filter.xml",
        "security/ir_model_access/olap_schema_table.xml",
        "security/ir_model_access/olap_schema_table_column.xml",
        "data/config_parameter_data.xml",
        "menu.xml",
        "views/olap_dashboard.xml",
        "views/olap_schema_table.xml",
    ],
}
