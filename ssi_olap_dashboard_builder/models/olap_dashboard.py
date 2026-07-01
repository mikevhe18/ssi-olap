# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OlapDashboard(models.Model):
    _name = "olap.dashboard"
    _description = "OLAP Dashboard Builder"
    _order = "sort_order, name"

    name = fields.Char(required=True)
    description = fields.Text()
    chart_type = fields.Selection(
        [
            ("bar", "Bar"),
            ("line", "Line"),
            ("pie", "Pie"),
            ("table", "Table"),
            ("kpi", "KPI"),
        ],
        required=True,
        default="bar",
    )
    ch_query = fields.Text(string="ClickHouse Query", required=True)
    x_axis = fields.Char(string="Kolom X")
    y_axis = fields.Char(string="Kolom Y")
    x_label = fields.Char(string="Label X")
    y_label = fields.Char(string="Label Y")
    sort_order = fields.Integer(default=10)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("published", "Published"),
        ],
        default="draft",
        required=True,
        copy=False,
    )

    preview_columns = fields.Text(string="Preview Columns (JSON)", readonly=True, copy=False)
    preview_data = fields.Text(string="Preview Data (JSON)", readonly=True, copy=False)
    go_report_id = fields.Char(string="Go Report ID", readonly=True, copy=False)

    created_by = fields.Char(default=lambda self: self.env.user.name, readonly=True)

    # ── Actions — diimplementasikan penuh di Sprint 6D ─────────────────────────
    # Stub di sini memvalidasi state dan memberi pesan jelas, bukan diam-diam
    # tidak melakukan apa-apa, supaya form tetap aman diklik sebelum 6D selesai.

    def action_validate(self):
        self.ensure_one()
        raise UserError(_("Validate & Preview akan diimplementasikan di Sprint 6D."))

    def action_publish(self):
        self.ensure_one()
        if self.state != "validated":
            raise UserError(_("Report harus divalidasi terlebih dahulu sebelum publish."))
        raise UserError(_("Publish to Dashboard akan diimplementasikan di Sprint 6D."))

    def action_update(self):
        self.ensure_one()
        if self.state != "published":
            raise UserError(_("Report belum dipublish."))
        raise UserError(_("Update akan diimplementasikan di Sprint 6D."))

    def action_unpublish(self):
        self.ensure_one()
        if self.state != "published":
            raise UserError(_("Report belum dipublish."))
        raise UserError(_("Unpublish akan diimplementasikan di Sprint 6D."))

    def action_open_dashboard(self):
        self.ensure_one()
        raise UserError(_("Open Dashboard akan diimplementasikan di Sprint 6D."))
