# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class OlapDashboard(models.Model):
    """
    Represents a custom ClickHouse report definition that can be validated
    against, and published to, the OLAP Platform's Go dashboard service.
    Publishing/unpublishing this record calls the Go API server-to-server
    so the report becomes visible in the Go dashboard's "Custom Reports"
    section. The ``note`` field inherited from ``mixin.master_data`` is
    used as the report's short description.
    """

    _name = "olap_dashboard"
    _inherit = ["mixin.master_data", "olap.api.mixin"]
    _description = "OLAP Dashboard Builder"
    _order = "sort_order, name"

    code = fields.Char(
        default="/",
    )
    chart_type = fields.Selection(
        string="Chart Type",
        selection=[
            ("bar", "Bar"),
            ("line", "Line"),
            ("pie", "Pie"),
            ("table", "Table"),
            ("kpi", "KPI"),
        ],
        required=True,
        default="bar",
        help="Visualization type used to render the report on the Go dashboard.",
    )
    ch_query = fields.Text(
        string="ClickHouse Query",
        help="SELECT query executed against the ClickHouse analytics database. "
        "Wajib diisi kecuali untuk Parent Menu (lihat is_parent_menu) — "
        "ditegakkan lewat _check_ch_query, bukan required=True, supaya "
        "Parent Menu tidak perlu isi query palsu.",
    )
    x_axis = fields.Char(
        string="X-Axis Column",
        help="Name of the result column plotted on the X axis.",
    )
    y_axis = fields.Char(
        string="Y-Axis Column",
        help="Name of the result column plotted on the Y axis.",
    )
    x_label = fields.Char(
        string="X-Axis Label",
        help="Label displayed for the X axis on the chart.",
    )
    y_label = fields.Char(
        string="Y-Axis Label",
        help="Label displayed for the Y axis on the chart.",
    )
    sort_order = fields.Integer(
        default=10,
        help="Determines the display order of this report on the Go dashboard.",
    )
    is_parent_menu = fields.Boolean(
        string="Ini Parent Menu (Grup)",
        default=False,
        help="Kalau dicentang, record ini HANYA jadi menu pengelompokan di "
        "submenu-bar dashboard — tidak punya query/chart sendiri (tab "
        "Query/Chart Configuration/Filters/Referensi Tabel/Preview "
        "disembunyikan). Laporan lain bisa memilih record ini lewat "
        "'Tampilkan di Bawah Menu' supaya masuk sebagai sub-item, bukan "
        "tampil sejajar di baris menu utama.",
    )
    parent_menu_id = fields.Many2one(
        string="Tampilkan di Bawah Menu",
        comodel_name="olap_dashboard",
        domain="[('is_parent_menu', '=', True), ('state', '=', 'published')]",
        ondelete="restrict",
        help="Opsional — pilih Parent Menu (harus sudah di-Publish dulu) "
        "supaya laporan ini dikelompokkan sebagai sub-item di bawahnya, "
        "bukan tampil sejajar di baris menu dashboard.",
    )
    filter_ids = fields.One2many(
        string="Filters",
        comodel_name="olap_dashboard_filter",
        inverse_name="dashboard_id",
        help="Filter controls shown above the report's chart on the Go "
        "dashboard (the .ctrl-bar, ala 'Performance Inventory'). Leave "
        "empty for a report with no filters — the 'Tampilkan' button still "
        "shows, just with nothing to configure.",
    )

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("published", "Published"),
        ],
        default="draft",
        required=True,
        copy=False,
        help=(
            "Report status: Draft = not yet checked, "
            "Validated = query checked successfully against ClickHouse, "
            "Published = live on the Go dashboard."
        ),
    )

    preview_columns = fields.Text(
        string="Preview Columns (JSON)",
        readonly=True,
        copy=False,
        help="JSON list of column names returned by the last successful validation.",
    )
    preview_data = fields.Text(
        string="Preview Data (JSON)",
        readonly=True,
        copy=False,
        help="JSON sample rows returned by the last successful validation.",
    )
    go_report_id = fields.Char(
        string="Go Report ID",
        readonly=True,
        copy=False,
        help="Identifier assigned by the Go API once this report is published.",
    )

    created_by = fields.Char(
        default=lambda self: self.env.user.name,
        readonly=True,
        help="Name of the user who created this dashboard definition.",
    )

    schema_reference = fields.Text(
        string="Referensi Tabel",
        readonly=True,
        copy=False,
        help="Struktur tabel ClickHouse (odoo_analytics) yang bisa dipakai "
        "di ClickHouse Query — diambil langsung dari server lewat tombol "
        "'Lihat Struktur Tabel', bukan dokumentasi statis.",
    )

    @api.constrains("is_parent_menu", "ch_query")
    def _check_ch_query(self):
        for record in self:
            if not record.is_parent_menu and not (record.ch_query or "").strip():
                raise ValidationError(
                    _(
                        "ClickHouse Query wajib diisi kecuali record ini "
                        "adalah Parent Menu."
                    )
                )

    @api.constrains("is_parent_menu", "parent_menu_id")
    def _check_no_nested_parent_menu(self):
        for record in self:
            if record.is_parent_menu and record.parent_menu_id:
                raise ValidationError(
                    _(
                        "Parent Menu tidak boleh punya Parent Menu lain — "
                        "hanya satu tingkat pengelompokan yang didukung."
                    )
                )

    # ── Go API helpers ───────────────────────────────────────────────────────
    # _get_param/_api_url/_dashboard_url/_api_key/_call_api now live in
    # olap.api.mixin (olap_api_mixin.py), shared with olap_schema_table.

    def _prepare_filters_payload(self):
        self.ensure_one()
        return [f._prepare_payload() for f in self.filter_ids]

    def _prepare_report_payload(self):
        self.ensure_one()
        return {
            "name": self.name,
            "description": self.note or "",
            "chart_type": self.chart_type,
            "query": self.ch_query or "",
            "x_axis": self.x_axis or "",
            "y_axis": self.y_axis or "",
            "x_label": self.x_label or "",
            "y_label": self.y_label or "",
            "sort_order": self.sort_order or 0,
            "created_by": self.env.user.name,
            "filters": self._prepare_filters_payload(),
            "is_parent_menu": self.is_parent_menu,
            "parent_menu_id": self.parent_menu_id.go_report_id
            if self.parent_menu_id
            else "",
        }

    @staticmethod
    def _reload():
        return {"type": "ir.actions.client", "tag": "reload"}

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_load_schema(self):
        for record in self.sudo():
            record._load_schema()
        return self._reload()

    def _load_schema(self):
        self.ensure_one()
        tables = self._call_api("GET", "/api/custom-reports/schema")
        lines = [
            "PENTING sebelum menulis query:",
            "",
            '1. Semua tabel WAJIB pakai prefix "odoo_analytics." — nama ini'
            " adalah nama database ClickHouse-nya, bukan opsional. Contoh:",
            "     FROM odoo_analytics.account_move",
            "",
            "2. WAJIB tambahkan FINAL setelah nama tabel, contoh:",
            "     FROM odoo_analytics.account_move FINAL",
            "   Tabel-tabel ini pakai engine ReplacingMergeTree (data masuk"
            " lewat CDC/replikasi bertahap) — tanpa FINAL, query bisa"
            " mengembalikan baris duplikat/versi basi dari record yang sama.",
            "",
            "3. Kolom __deleted menandai record yang sudah dihapus di Odoo"
            " (soft-delete ikut ter-replikasi, bukan benar-benar hilang dari"
            " ClickHouse). Biasanya perlu ditambahkan:",
            "     WHERE __deleted != 'true'",
            "   supaya data yang sudah dihapus di Odoo tidak ikut terhitung.",
            "",
            "4. Nama tabel ClickHouse = nama model Odoo dengan tanda titik (.)"
            ' diganti garis bawah (_) — kolom "model Odoo" di bawah ini'
            " sudah menunjukkan padanannya per tabel.",
            "",
            "Contoh query lengkap yang menggabungkan semua poin di atas:",
            "  SELECT move_type, count() AS jumlah",
            "  FROM odoo_analytics.account_move FINAL",
            "  WHERE __deleted != 'true'",
            "  GROUP BY move_type",
            "",
            "=" * 60,
            "DAFTAR TABEL & KOLOM (diambil langsung dari server saat ini)",
            "=" * 60,
            "",
        ]
        for table in tables:
            lines.append(
                "=== %s (model Odoo: %s) ==="
                % (table["table"], table["odoo_model"])
            )
            for column in table["columns"]:
                line = "  %-20s %s" % (column["name"], column["type"])
                if column.get("note"):
                    line += "  -- %s" % column["note"]
                lines.append(line)
            lines.append("")
        self.write({"schema_reference": "\n".join(lines)})

    def action_validate(self):
        for record in self.sudo():
            record._validate()
        return self._reload()

    def _validate(self):
        self.ensure_one()
        if not self.ch_query or not self.ch_query.strip():
            error_message = """
Context: Validate dashboard query
Database ID: %s
Problem: Query is empty
Solution: Fill in the ClickHouse Query field before validating
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        data = self._call_api(
            "POST",
            "/api/custom-reports/validate",
            {"query": self.ch_query, "filters": self._prepare_filters_payload()},
        )
        if not data.get("valid"):
            error_message = """
Context: Validate dashboard query
Database ID: %s
Problem: Query rejected by Go API (%s)
Solution: Fix the ClickHouse query and validate again
""" % (
                self.id,
                data.get("error"),
            )
            raise UserError(_(error_message))
        self.write(
            {
                "preview_columns": json.dumps(
                    data.get("columns", []), ensure_ascii=False
                ),
                "preview_data": json.dumps(
                    data.get("preview", []), indent=2, ensure_ascii=False
                ),
                "state": "validated",
            }
        )

    def action_publish(self):
        for record in self.sudo():
            record._publish()
        return self._reload()

    def _publish(self):
        self.ensure_one()
        # Parent Menu tidak punya query untuk divalidasi — boleh publish
        # langsung dari draft.
        if self.state != "validated" and not self.is_parent_menu:
            error_message = """
Context: Publish dashboard to Go
Database ID: %s
Problem: Report has not been validated yet
Solution: Run 'Validate & Preview' before publishing
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        data = self._call_api(
            "POST", "/api/custom-reports", self._prepare_report_payload()
        )
        report_id = data.get("ID") or data.get("id")
        if not report_id:
            error_message = """
Context: Publish dashboard to Go
Database ID: %s
Problem: Go API did not return a report ID
Solution: Check the Go API server logs and try again
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        self.write({"go_report_id": report_id, "state": "published"})

    def action_update(self):
        for record in self.sudo():
            record._update()
        return self._reload()

    def _update(self):
        self.ensure_one()
        if self.state != "published":
            error_message = """
Context: Update published dashboard on Go
Database ID: %s
Problem: Report has not been published yet
Solution: Publish the report before trying to update it
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        self._call_api(
            "PUT",
            "/api/custom-reports/%s" % self.go_report_id,
            self._prepare_report_payload(),
        )

    def action_unpublish(self):
        for record in self.sudo():
            record._unpublish()
        return self._reload()

    def _unpublish(self):
        self.ensure_one()
        if self.state != "published":
            error_message = """
Context: Unpublish dashboard from Go
Database ID: %s
Problem: Report has not been published yet
Solution: Nothing to unpublish - report is already unpublished
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        if self.is_parent_menu:
            children = self.search(
                [("parent_menu_id", "=", self.id), ("state", "=", "published")]
            )
            if children:
                error_message = """
Context: Unpublish Parent Menu from Go
Database ID: %s
Problem: %s laporan lain masih menunjuk ke Parent Menu ini (%s)
Solution: Pindahkan/unpublish laporan-laporan itu dulu sebelum unpublish \
Parent Menu ini
""" % (
                    self.id,
                    len(children),
                    ", ".join(children.mapped("name")),
                )
                raise UserError(_(error_message))
        self._call_api("DELETE", "/api/custom-reports/%s" % self.go_report_id)
        self.write({"state": "draft", "go_report_id": False})

    def action_open_dashboard(self):
        for record in self.sudo():
            result = record._open_dashboard()
        return result

    def _open_dashboard(self):
        self.ensure_one()
        if not self.go_report_id:
            error_message = """
Context: Open dashboard
Database ID: %s
Problem: Report has not been published yet
Solution: Publish the report before opening it on the dashboard
""" % (
                self.id,
            )
            raise UserError(_(error_message))
        return {
            "type": "ir.actions.act_url",
            "url": "%s/custom-reports/%s" % (self._dashboard_url(), self.go_report_id),
            "target": "new",
        }
