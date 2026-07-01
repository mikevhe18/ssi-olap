# -*- coding: utf-8 -*-
import json
import logging

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

API_TIMEOUT = 15


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

    # ── Konfigurasi Go API (System Parameters) ─────────────────────────────────

    def _get_param(self, key):
        value = self.env["ir.config_parameter"].sudo().get_param(key)
        if not value:
            raise UserError(_("System Parameter '%s' belum diisi.") % key)
        return value

    def _api_url(self):
        return self._get_param("olap.go_api_url").rstrip("/")

    def _dashboard_url(self):
        return self._get_param("olap.go_dashboard_url").rstrip("/")

    def _api_key(self):
        return self._get_param("olap.go_api_key")

    # ── Go API helpers ──────────────────────────────────────────────────────────

    def _call_api(self, method, path, payload=None):
        """POST/PUT/DELETE ke Go API. Selalu kirim X-API-Key. Melempar UserError
        dengan pesan dari Go kalau status >= 400 atau body bukan JSON valid."""
        url = self._api_url() + path
        headers = {"Content-Type": "application/json", "X-API-Key": self._api_key()}
        try:
            resp = requests.request(
                method,
                url,
                headers=headers,
                data=json.dumps(payload) if payload is not None else None,
                timeout=API_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            _logger.exception("olap.dashboard: gagal menghubungi Go API %s", url)
            raise UserError(_("Gagal menghubungi Go API (%s): %s") % (url, e))

        try:
            data = resp.json()
        except ValueError:
            raise UserError(
                _("Respons Go API tidak valid (status %s): %s")
                % (resp.status_code, resp.text[:300])
            )
        if resp.status_code >= 400:
            raise UserError(data.get("error") or _("Go API error (status %s)") % resp.status_code)
        return data

    def _report_payload(self):
        self.ensure_one()
        return {
            "name": self.name,
            "description": self.description or "",
            "chart_type": self.chart_type,
            "query": self.ch_query,
            "x_axis": self.x_axis or "",
            "y_axis": self.y_axis or "",
            "x_label": self.x_label or "",
            "y_label": self.y_label or "",
            "sort_order": self.sort_order or 0,
            "created_by": self.env.user.name,
        }

    @staticmethod
    def _reload():
        return {"type": "ir.actions.client", "tag": "reload"}

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_validate(self):
        self.ensure_one()
        if not self.ch_query or not self.ch_query.strip():
            raise UserError(_("Query tidak boleh kosong."))
        data = self._call_api(
            "POST", "/api/custom-reports/validate", {"query": self.ch_query}
        )
        if not data.get("valid"):
            raise UserError(data.get("error") or _("Query tidak valid."))
        self.write(
            {
                "preview_columns": json.dumps(data.get("columns", []), ensure_ascii=False),
                "preview_data": json.dumps(
                    data.get("preview", []), indent=2, ensure_ascii=False
                ),
                "state": "validated",
            }
        )
        return self._reload()

    def action_publish(self):
        self.ensure_one()
        if self.state != "validated":
            raise UserError(_("Report harus divalidasi terlebih dahulu sebelum publish."))
        data = self._call_api("POST", "/api/custom-reports", self._report_payload())
        report_id = data.get("ID") or data.get("id")
        if not report_id:
            raise UserError(_("Go API tidak mengembalikan ID report."))
        self.write({"go_report_id": report_id, "state": "published"})
        return self._reload()

    def action_update(self):
        self.ensure_one()
        if self.state != "published":
            raise UserError(_("Report belum dipublish."))
        self._call_api(
            "PUT", "/api/custom-reports/%s" % self.go_report_id, self._report_payload()
        )
        return self._reload()

    def action_unpublish(self):
        self.ensure_one()
        if self.state != "published":
            raise UserError(_("Report belum dipublish."))
        self._call_api("DELETE", "/api/custom-reports/%s" % self.go_report_id)
        self.write({"state": "draft", "go_report_id": False})
        return self._reload()

    def action_open_dashboard(self):
        self.ensure_one()
        if not self.go_report_id:
            raise UserError(_("Report belum dipublish."))
        return {
            "type": "ir.actions.act_url",
            "url": "%s/custom-reports/%s" % (self._dashboard_url(), self.go_report_id),
            "target": "new",
        }
