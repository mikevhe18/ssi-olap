# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

# Must match customreports.nameRe on the Go side — the filter's technical
# name has to line up with a {name:Type} placeholder the report author
# writes into ch_query.
NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class OlapDashboardFilter(models.Model):
    """
    One filter control rendered above a custom report's chart (the
    ``.ctrl-bar``, ala the "Performance Inventory" page) — dashboard viewers
    fill these in and click "Tampilkan" to re-run the report's query with
    their chosen values, bound through ClickHouse's native parameterized
    query mechanism on the Go side.
    """

    _name = "olap_dashboard_filter"
    _description = "OLAP Dashboard Filter"
    _order = "sequence, id"

    dashboard_id = fields.Many2one(
        string="Dashboard",
        comodel_name="olap_dashboard",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(
        default=10,
    )
    name = fields.Char(
        string="Param Name",
        required=True,
        help="Must match a {name:Type} placeholder in the report's ClickHouse "
        "Query, e.g. 'dateFrom' for a {dateFrom:Date} placeholder. Letters, "
        "numbers, underscore only, can't start with a number.",
    )
    label = fields.Char(
        string="Label",
        required=True,
        help="Text shown next to the filter control on the dashboard.",
    )
    filter_type = fields.Selection(
        string="Type",
        selection=[
            ("date", "Date"),
            ("select", "Dropdown"),
            ("number", "Number"),
            ("text", "Text"),
        ],
        required=True,
        default="text",
    )
    default_value = fields.Char(
        string="Default Value",
        help="Pre-filled value, and the value used when validating/previewing "
        "the query in Odoo (there's no interactive filter bar at authoring "
        "time).",
    )
    options = fields.Text(
        string="Dropdown Options",
        help="Only used when Type = Dropdown. One option per line, formatted "
        "as 'value|label' (e.g. 'sale|Penjualan (Invoice)'). If a line has "
        "no '|', the same text is used as both value and label.",
    )

    @api.constrains("name")
    def _check_name(self):
        for record in self:
            if not NAME_RE.match(record.name or ""):
                raise ValidationError(
                    _(
                        "Param Name '%s' is invalid — letters, numbers, "
                        "underscore only, can't start with a number."
                    )
                    % record.name
                )

    @api.constrains("filter_type", "options")
    def _check_options(self):
        for record in self:
            if record.filter_type == "select" and not record._parse_options():
                raise ValidationError(
                    _("Filter '%s' is a Dropdown but has no Dropdown Options.")
                    % record.name
                )

    def _parse_options(self):
        self.ensure_one()
        result = []
        for line in (self.options or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if "|" in line:
                value, label = line.split("|", 1)
            else:
                value = label = line
            result.append({"value": value.strip(), "label": label.strip()})
        return result

    def _prepare_payload(self):
        self.ensure_one()
        item = {
            "name": self.name,
            "label": self.label,
            "type": self.filter_type,
            "default": self.default_value or "",
        }
        if self.filter_type == "select":
            item["options"] = self._parse_options()
        return item
