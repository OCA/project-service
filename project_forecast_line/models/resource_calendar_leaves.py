# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import api, models


class ResourceCalendarLeaves(models.Model):
    _name = "resource.calendar.leaves"
    _inherit = ["resource.calendar.leaves", "forecast.line.mixin"]

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        recs._update_forecast_lines()
        return recs

    def write(self, values):
        res = super().write(values)
        self._update_forecast_lines()
        return res

    def _get_resource_roles(self):
        resources = self.mapped("resource_id")
        if resources:
            employees = self.env["hr.employee"].search([("id", "in", resources.ids)])
        else:
            employees = self.env["hr.employee"].search(
                [("company_id", "in", self.mapped("company_id").ids)]
            )
        roles = self.env["hr.employee.forecast.role"].search(
            [("employee_id", "in", employees.ids)]
        )
        return roles

    def _update_forecast_lines(self):
        roles = self._get_resource_roles()
        if self:
            date_start = min(self.mapped("date_from")).date() - relativedelta(days=1)
            date_to = max(self.mapped("date_to")).date() + relativedelta(days=1)
        else:
            date_start = date_to = None
        roles.with_context(
            date_start=date_start, date_to=date_to
        )._update_forecast_lines()

    def unlink(self):
        roles = self._get_resource_roles()
        res = super().unlink()
        roles._update_forecast_lines()
        return res
