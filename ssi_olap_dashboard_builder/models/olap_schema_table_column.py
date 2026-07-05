# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

# Must match provisioning.identRe on the Go side (provisioning/validate.go)
# — lowercase only, unlike olap_dashboard_filter.NAME_RE (filter param names,
# a different concern), because this is a real Postgres/ClickHouse column
# name and both are always lowercase snake_case by Odoo's own _table/_column
# convention.
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Must match provisioning.allowedCHTypes on the Go side (provisioning/validate.go).
CH_TYPE_SELECTION = [
    ("Int64", "Int64"),
    ("Int32", "Int32"),
    ("Float64", "Float64"),
    ("String", "String"),
    ("UInt8", "UInt8 (boolean 0/1)"),
    ("DateTime64(3)", "DateTime64(3)"),
    ("DateTime", "DateTime"),
]


class OlapSchemaTableColumn(models.Model):
    """
    One column of a ClickHouse table being provisioned from Odoo (see
    ``olap_schema_table``) — name + ClickHouse type the user picks/confirms,
    optionally pre-filled from the real Postgres column via "Muat Kolom dari
    PostgreSQL" (``pg_type``/``note`` are informational only, never enforced).
    """

    _name = "olap_schema_table_column"
    _description = "OLAP Schema Table Column"
    _order = "sequence, id"

    table_id = fields.Many2one(
        string="Tabel",
        comodel_name="olap_schema_table",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(
        default=10,
    )
    name = fields.Char(
        string="Nama Kolom",
        required=True,
        help="Huruf kecil, angka, underscore saja, harus diawali huruf — "
        "harus sama persis dengan validasi di sisi Go (provisioning/validate.go).",
    )
    pg_type = fields.Char(
        string="Tipe PostgreSQL",
        readonly=True,
        help="Informasi saja (dari 'Muat Kolom dari PostgreSQL') — tidak "
        "dikirim ke ClickHouse.",
    )
    ch_type = fields.Selection(
        string="Tipe ClickHouse",
        selection=CH_TYPE_SELECTION,
        required=True,
        default="String",
        help="Tipe ClickHouse final yang akan dipakai — boleh disunting "
        "walau ada saran dari 'Muat Kolom dari PostgreSQL'.",
    )
    note = fields.Char(
        string="Catatan",
        readonly=True,
        help="Catatan otomatis (mis. kolom tanggal Postgres disimpan "
        "sebagai integer hari-sejak-epoch di ClickHouse) — informasi saja.",
    )

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not NAME_RE.match(record.name or ""):
                raise ValidationError(
                    _(
                        "Nama Kolom '%s' tidak valid — huruf kecil, angka, "
                        "underscore saja, harus diawali huruf."
                    )
                    % record.name
                )

    def _prepare_payload(self):
        self.ensure_one()
        return {"name": self.name, "ch_type": self.ch_type}
