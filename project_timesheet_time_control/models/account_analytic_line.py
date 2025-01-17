# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Sergio Teruel
# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    _order = "date_time desc"

    date_time = fields.Datetime(
        string="Start Time", default=fields.Datetime.now, copy=False
    )
    date_time_end = fields.Datetime(
        string="End Time",
        compute="_compute_date_time_end",
        inverse="_inverse_date_time_end",
    )
    show_time_control = fields.Selection(
        selection=[("resume", "Resume"), ("stop", "Stop")],
        compute="_compute_show_time_control",
        help="Indicate which time control button to show, if any.",
    )

    @api.depends("date_time", "unit_amount", "product_uom_id")
    def _compute_date_time_end(self):
        hour_uom = self.env.ref("uom.product_uom_hour")
        for record in self:
            if (
                record.product_uom_id == hour_uom
                and record.date_time
                and record.unit_amount
            ):
                record.date_time_end = record.date_time + relativedelta(
                    hours=record.unit_amount
                )
            else:
                record.date_time_end = record.date_time_end

    def _inverse_date_time_end(self):
        hour_uom = self.env.ref("uom.product_uom_hour")
        for record in self.filtered(lambda x: x.date_time and x.date_time_end):
            if record.product_uom_id == hour_uom:
                record.unit_amount = (
                    record.date_time_end - record.date_time
                ).seconds / 3600

    @api.model
    def _eval_date(self, vals):
        if vals.get("date_time"):
            return dict(vals, date=self._convert_datetime_to_date(vals["date_time"]))
        return vals

    def _convert_datetime_to_date(self, datetime_):
        if isinstance(datetime_, str):
            datetime_ = fields.Datetime.from_string(datetime_)
        return fields.Date.context_today(self, datetime_)

    @api.model
    def _running_domain(self):
        """Domain to find running timesheet lines."""
        return [
            ("date_time", "!=", False),
            ("user_id", "=", self.env.user.id),
            ("project_id.allow_timesheets", "=", True),
            ("unit_amount", "=", 0),
        ]

    @api.model
    def _duration(self, start, end):
        """Compute float duration between start and end."""
        try:
            return (end - start).total_seconds() / 3600
        except TypeError:
            return 0

    @api.depends("employee_id", "unit_amount")
    def _compute_show_time_control(self):
        """Decide when to show time controls."""
        for one in self:
            if one.employee_id not in self.env.user.employee_ids:
                one.show_time_control = False
            elif one.unit_amount or not one.date_time:
                one.show_time_control = "resume"
            else:
                one.show_time_control = "stop"

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(list(map(self._eval_date, vals_list)))

    def write(self, vals):
        return super().write(self._eval_date(vals))

    def button_resume_work(self):
        """Create a new record starting now, with a running timer."""
        return {
            "name": _("Resume work"),
            "res_model": "hr.timesheet.switch",
            "target": "new",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
        }

    def button_end_work(self):
        end = fields.Datetime.to_datetime(
            self.env.context.get("stop_dt", datetime.now())
        )
        for line in self:
            if line.unit_amount:
                raise UserError(
                    _(
                        "Cannot stop timer %d because it is not running. "
                        "Refresh the page and check again."
                    )
                    % line.id
                )
            line.unit_amount = line._duration(line.date_time, end)
        return True
