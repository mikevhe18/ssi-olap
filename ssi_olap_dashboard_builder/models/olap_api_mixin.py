# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

API_TIMEOUT = 15


class OlapApiMixin(models.AbstractModel):
    """
    Shared server-to-server call helper to the Go API — used by both
    ``olap_dashboard`` (report CRUD) and ``olap_schema_table`` (ClickHouse
    schema provisioning), so the system-parameter lookup and error-message
    formatting only live in one place.
    """

    _name = "olap.api.mixin"
    _description = "OLAP Go API Call Mixin"

    def _get_param(self, key):
        value = self.env["ir.config_parameter"].sudo().get_param(key)
        if not value:
            error_message = """
Context: Read Go API system parameter
Problem: System parameter '%s' is not configured
Solution: Set the parameter value in Settings > Technical > System Parameters
""" % (
                key,
            )
            raise UserError(_(error_message))
        return value

    def _api_url(self):
        return self._get_param("olap.go_api_url").rstrip("/")

    def _dashboard_url(self):
        return self._get_param("olap.go_dashboard_url").rstrip("/")

    def _api_key(self):
        return self._get_param("olap.go_api_key")

    def _call_api(self, method, path, payload=None):
        self.ensure_one()
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
            _logger.exception("olap_api_mixin: failed to reach Go API %s", url)
            error_message = """
Context: Call Go API
Database ID: %s
Problem: Unable to reach Go API at %s (%s)
Solution: Check network connectivity and the 'olap.go_api_url' system parameter
""" % (
                self.id,
                url,
                e,
            )
            raise UserError(_(error_message))

        try:
            data = resp.json()
        except ValueError:
            error_message = """
Context: Call Go API
Database ID: %s
Problem: Go API returned a non-JSON response (status %s): %s
Solution: Check the Go API server logs for the underlying error
""" % (
                self.id,
                resp.status_code,
                resp.text[:300],
            )
            raise UserError(_(error_message))
        if resp.status_code >= 400:
            error_message = """
Context: Call Go API
Database ID: %s
Problem: Go API returned error (status %s): %s
Solution: Fix the reported issue and try again
""" % (
                self.id,
                resp.status_code,
                data.get("error"),
            )
            raise UserError(_(error_message))
        return data
