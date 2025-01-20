# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class HrLeave(models.Model):
    _name = "hr.leave"
    _inherit = ["hr.leave", "forecast.line.mixin"]

    @api.model_create_multi
    def create(self, vals_list):
        leaves = super().create(vals_list)
        leaves._update_forecast_lines()
        return leaves

    def write(self, values):
        res = super().write(values)
        self._update_forecast_lines()
        return res

    def _update_forecast_lines(self):
        forecast_vals = []
        ForecastLine = self.env["forecast.line"].sudo()
        # XXX try to be smarter and only unlink those needing unlinking, update the others
        ForecastLine.search(
            [("res_id", "in", self.ids), ("res_model", "=", self._name)]
        ).unlink()
        leaves = self.filtered_domain([("state", "!=", "refuse")])
        # we need to use sudo here, because forecast line creation
        # requires access to fields declared on hr.employee
        # we don't want to restrict them with `groups="hr.group_hr_user"`
        # as this will require giving access to employee app,
        # which isn't wanted on some projects
        # for more details see here: .../addons/hr/models/hr_employee.py#L22
        for leave in leaves.sudo():
            if not leave.employee_id.main_role_id:
                _logger.warning(
                    "No forecast role for employee %s (%s)",
                    leave.employee_id.name,
                    leave.employee_id,
                )
                continue
            if leave.state == "validate":
                # will be handled by the resource.calendar.leaves
                continue
            else:
                forecast_type = "forecast"
            ForecastLine = ForecastLine.with_company(leave.employee_company_id)
            forecast_vals += ForecastLine._prepare_forecast_lines(
                name=_("Leave"),
                date_from=leave.date_from.date(),
                date_to=leave.date_to.date(),
                ttype=forecast_type,
                forecast_hours=ForecastLine.convert_days_to_hours(
                    -1 * leave.number_of_days
                ),
                unit_cost=leave.employee_id.hourly_cost,
                forecast_role_id=leave.employee_id.main_role_id.id,
                hr_leave_id=leave.id,
                employee_id=leave.employee_id.id,
                res_model=self._name,
                res_id=leave.id,
            )
        return ForecastLine.create(forecast_vals)

    @api.model
    def _recompute_forecast_lines(self, force_company_id=None):
        today = fields.Date.context_today(self)
        if force_company_id:
            companies = self.env["res.company"].browse(force_company_id)
        else:
            companies = self.env["res.company"].search([])
        for company in companies:
            to_update = self.with_company(company).search(
                [
                    ("date_to", ">=", today),
                    ("employee_company_id", "=", company.id),
                ]
            )
            to_update._update_forecast_lines()


# XXX: leave request should create forcast negative forecast?
