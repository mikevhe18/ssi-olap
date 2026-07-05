# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo_yaml_test import YamlTransactionCase

from odoo.exceptions import UserError
from odoo.tests import tagged


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.text = str(payload)
        self._payload = payload

    def json(self):
        return self._payload


@tagged("post_install", "-at_install")
class TestOlapDashboard(YamlTransactionCase):
    def test_olap_dashboard(self):
        self.run_yaml_scenario("test_data_olap_dashboard.yaml")

    def _create_dashboard(self):
        return self.env["olap_dashboard"].create(
            {
                "name": "Test Dashboard",
                "ch_query": "SELECT 1",
            }
        )

    def test_validate_empty_query_raises(self):
        """Validating a dashboard without a query must fail before any API call."""
        dashboard = self._create_dashboard()
        dashboard.ch_query = "   "
        with self.assertRaises(UserError):
            dashboard.action_validate()

    def test_publish_without_validation_raises(self):
        """Publishing a dashboard still in draft must fail before any API call."""
        dashboard = self._create_dashboard()
        with self.assertRaises(UserError):
            dashboard.action_publish()

    def test_open_dashboard_without_publish_raises(self):
        """Opening the dashboard before publishing must fail."""
        dashboard = self._create_dashboard()
        with self.assertRaises(UserError):
            dashboard.action_open_dashboard()

    @patch(
        "odoo.addons.ssi_olap_dashboard_builder.models.olap_dashboard.requests.request"
    )
    def test_validate_success_fills_preview(self, mock_request):
        mock_request.return_value = FakeResponse(
            200,
            {
                "valid": True,
                "columns": ["col_a"],
                "preview": [{"col_a": 1}],
            },
        )
        dashboard = self._create_dashboard()
        dashboard.action_validate()
        self.assertEqual(dashboard.state, "validated")
        self.assertIn("col_a", dashboard.preview_columns)
        self.assertIn("col_a", dashboard.preview_data)

    @patch(
        "odoo.addons.ssi_olap_dashboard_builder.models.olap_dashboard.requests.request"
    )
    def test_publish_update_unpublish_flow(self, mock_request):
        dashboard = self._create_dashboard()

        mock_request.return_value = FakeResponse(200, {"valid": True})
        dashboard.action_validate()
        self.assertEqual(dashboard.state, "validated")

        mock_request.return_value = FakeResponse(200, {"id": "42"})
        dashboard.action_publish()
        self.assertEqual(dashboard.state, "published")
        self.assertEqual(dashboard.go_report_id, "42")

        mock_request.return_value = FakeResponse(200, {})
        dashboard.action_update()
        self.assertEqual(dashboard.state, "published")

        result = dashboard.action_open_dashboard()
        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertIn("42", result["url"])

        mock_request.return_value = FakeResponse(200, {})
        dashboard.action_unpublish()
        self.assertEqual(dashboard.state, "draft")
        self.assertFalse(dashboard.go_report_id)

    @patch(
        "odoo.addons.ssi_olap_dashboard_builder.models.olap_dashboard.requests.request"
    )
    def test_publish_without_report_id_raises(self, mock_request):
        dashboard = self._create_dashboard()
        mock_request.return_value = FakeResponse(200, {"valid": True})
        dashboard.action_validate()

        mock_request.return_value = FakeResponse(200, {})
        with self.assertRaises(UserError):
            dashboard.action_publish()

    @patch(
        "odoo.addons.ssi_olap_dashboard_builder.models.olap_dashboard.requests.request"
    )
    def test_call_api_error_status_raises(self, mock_request):
        mock_request.return_value = FakeResponse(400, {"error": "bad query"})
        dashboard = self._create_dashboard()
        with self.assertRaises(UserError):
            dashboard.action_validate()
