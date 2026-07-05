# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class OlapSchemaTable(models.Model):
    """
    Provisions a ClickHouse analytics table (the 3-object kafka_x/x/mv_x
    pipeline, see OLAP-ARCHITECTURE.md) directly from Odoo, for cases where
    a client needs a table/column set the shipped olap-modules schema
    doesn't cover (e.g. a newly installed Odoo module). Deliberately NOT
    generated from fields_get() — the user picks & confirms every column and
    its ClickHouse type themselves; "Muat Kolom dari PostgreSQL" only offers
    the real Postgres columns + a suggested type as a starting point.

    Only additive: once a table exists in ClickHouse, this can add new
    columns to it (draft -> provisioned stays provisioned), but never
    removes or retypes an existing column — see provisioning/chschema.go on
    the Go side, which is the actual enforcement point.
    """

    _name = "olap_schema_table"
    _inherit = ["olap.api.mixin"]
    _description = "OLAP Schema Table (ClickHouse Provisioning)"
    _order = "name"

    name = fields.Char(
        required=True,
    )
    pg_table = fields.Char(
        string="Tabel Postgres/ClickHouse",
        required=True,
        help="Nama tabel teknis di Postgres Odoo DAN di ClickHouse (sama "
        "persis) — mis. 'helpdesk_ticket'. Huruf kecil, angka, underscore "
        "saja.",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("provisioned", "Provisioned"),
        ],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        help="Draft = belum pernah di-provision ke ClickHouse. Provisioned "
        "= tabel sudah ada di ClickHouse (masih bisa ditambah kolom lewat "
        "'Provision ke ClickHouse' lagi).",
    )
    schema_version = fields.Integer(
        string="Versi Skema",
        default=1,
        readonly=True,
        copy=False,
        help="Naik setiap kali ada kolom baru ditambahkan ke tabel yang "
        "sudah live — dipakai sebagai suffix consumer group Kafka "
        "(clickhouse_<table>_v<versi>) saat kafka_x/mv_x di-recreate. "
        "Consumer group baru hanya membaca perubahan BARU (bukan snapshot "
        "ulang) — baris yang sudah ada sebelum kolom ini ditambahkan akan "
        "tetap kosong/default sampai baris itu di-update lagi di Odoo.",
    )
    column_ids = fields.One2many(
        string="Kolom",
        comodel_name="olap_schema_table_column",
        inverse_name="table_id",
        help="Kolom struktural (id, write_date, __deleted, _ingested_at) "
        "otomatis ditambahkan di sisi Go — cukup isi kolom bisnis yang "
        "relevan di sini.",
    )

    def _prepare_columns_payload(self):
        self.ensure_one()
        return [c._prepare_payload() for c in self.column_ids]

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_load_pg_columns(self):
        for record in self.sudo():
            record._load_pg_columns()
        return {"type": "ir.actions.client", "tag": "reload"}

    def _load_pg_columns(self):
        self.ensure_one()
        if not self.pg_table:
            error_message = """
Context: Load PostgreSQL columns
Database ID: %s
Problem: Tabel Postgres/ClickHouse belum diisi
Solution: Isi field 'Tabel Postgres/ClickHouse' dulu sebelum memuat kolom
""" % (
                self.id,
            )
            raise UserError(_(error_message))

        columns = self._call_api(
            "GET", "/api/schema/postgres-columns?table=%s" % self.pg_table
        )
        existing_names = set(self.column_ids.mapped("name"))
        new_rows = [
            (
                0,
                0,
                {
                    "name": col["name"],
                    "pg_type": col.get("pg_type", ""),
                    "ch_type": col.get("suggested_ch_type") or "String",
                    "note": col.get("note", ""),
                },
            )
            for col in columns
            if col["name"] not in existing_names
        ]
        if new_rows:
            self.write({"column_ids": new_rows})

    def action_provision(self):
        for record in self.sudo():
            record._provision()
        return {"type": "ir.actions.client", "tag": "reload"}

    def _provision(self):
        self.ensure_one()
        if not self.column_ids:
            error_message = """
Context: Provision ClickHouse table
Database ID: %s
Problem: Belum ada kolom yang diisi
Solution: Tambahkan minimal satu kolom (langsung atau lewat 'Muat Kolom \
dari PostgreSQL') sebelum provision
""" % (
                self.id,
            )
            raise UserError(_(error_message))

        data = self._call_api(
            "POST",
            "/api/schema/tables",
            {
                "table": self.pg_table,
                "schema_version": self.schema_version,
                "columns": self._prepare_columns_payload(),
            },
        )
        self.write(
            {
                "state": "provisioned",
                "schema_version": data.get("schema_version", self.schema_version),
            }
        )
