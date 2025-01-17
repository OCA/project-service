# Copyright 2019 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrTimesheetTimeControlMixin(models.AbstractModel):
    _name = "hr.timesheet.time_control.mixin"
    _description = "Mixin for records related with timesheet lines"

    show_time_control = fields.Selection(
        selection=[("start", "Start"), ("stop", "Stop")],
        compute="_compute_show_time_control",
        help="Indicate which time control button to show, if any.",
    )

    @api.model
    def _relation_with_timesheet_line(self):
        """Name of the field that relates this model with AAL."""
        raise NotImplementedError

    @api.model
    def _timesheet_running_domain(self):
        """Domain to find running timesheet lines."""
        return self.env["account.analytic.line"]._running_domain() + [
            (self._relation_with_timesheet_line(), "in", self.ids),
        ]

    def _compute_show_time_control(self):
        """Decide which time control button to show, if any."""
        related_field = self._relation_with_timesheet_line()
        grouped = self.env["account.analytic.line"].read_group(
            domain=self._timesheet_running_domain(),
            fields=["id"],
            groupby=[related_field],
        )
        lines_per_record = {
            group[related_field][0]: group[f"{related_field}_count"]
            for group in grouped
        }
        button_per_lines = {0: "start", 1: "stop"}
        for record in self:
            record.show_time_control = button_per_lines.get(
                lines_per_record.get(record.id, 0),
                False,
            )

    def button_start_work(self):
        """Create a new record starting now, with a running timer."""
        related_field = self._relation_with_timesheet_line()
        return {
            "context": {f"default_{related_field}": self.id},
            "name": _("Start work"),
            "res_model": "hr.timesheet.switch",
            "target": "new",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
        }

    def button_end_work(self):
        running_lines = self.env["account.analytic.line"].search(
            self._timesheet_running_domain(),
        )
        if not running_lines:
            model = self.env["ir.model"].sudo().search([("model", "=", self._name)])
            message = _(
                "No running timer found in %(model)s %(record)s. "
                "Refresh the page and check again."
            )
            raise UserError(
                message % {"model": model.name, "record": self.display_name}
            )
        return running_lines.button_end_work()
