# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = ["sale.order.line", "forecast.line.mixin"]

    forecast_date_start = fields.Date()
    forecast_date_end = fields.Date()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._update_forecast_lines()
        return lines

    def _update_forecast_lines(self):
        forecast_vals = []
        ForecastLine = self.env["forecast.line"].sudo()
        # XXX try to be smarter and only unlink those needing unlinking, update the others
        ForecastLine.search(
            [("res_id", "in", self.ids), ("res_model", "=", self._name)]
        ).unlink()
        for line in self:
            ForecastLine = ForecastLine.with_company(line.company_id)
            if not line.product_id.forecast_role_id:
                continue
            elif line.state in ("cancel", "sale"):
                # no forecast line for confirmed sales -> this is handled by projects and tasks
                continue
            elif not (line.forecast_date_end and line.forecast_date_start):
                _logger.info(
                    "sale line with forecast product but no dates -> ignoring %s",
                    line.id,
                )
                continue
            else:
                forecast_type = "forecast"
            uom = line.product_uom
            quantity_hours = uom._compute_quantity(
                line.product_uom_qty, self.env.ref("uom.product_uom_hour")
            )
            forecast_vals += ForecastLine._prepare_forecast_lines(
                name=line.name,
                date_from=line.forecast_date_start,
                date_to=line.forecast_date_end,
                ttype=forecast_type,
                forecast_hours=-1 * quantity_hours,
                unit_cost=line.product_id.standard_price,  # XXX currency + unit conversion
                forecast_role_id=line.product_id.forecast_role_id.id,
                sale_line_id=line.id,
                project_id=line.project_id.id,
                res_model="sale.order.line",
                res_id=line.id,
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
                    ("forecast_date_end", ">=", today),
                    ("company_id", "=", company.id),
                ]
            )
            to_update._update_forecast_lines()

    def _update_forecast_lines_trigger_fields(self):
        return [
            "state",
            "product_uom_qty",
            "forecast_date_start",
            "forecast_date_end",
            "product_id",
            "name",
        ]

    def _write(self, values):
        res = super()._write(values)
        trigger_fields = self._update_forecast_lines_trigger_fields()
        if any(field in values for field in trigger_fields):
            self._update_forecast_lines()
        return res

    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        res = super()._onchange_product_id_warning()
        for line in self:
            if not line.product_id.forecast_role_id:
                line.forecast_date_start = False
                line.forecast_date_end = False
            else:
                if (
                    not line.forecast_date_start
                    and line.order_id.default_forecast_date_start
                ):
                    line.forecast_date_start = line.order_id.default_forecast_date_start
                if (
                    not line.forecast_date_end
                    and line.order_id.default_forecast_date_end
                ):
                    line.forecast_date_end = line.order_id.default_forecast_date_end
        return res

    def _timesheet_create_task_prepare_values(self, project):
        values = super()._timesheet_create_task_prepare_values(project)
        values.update(
            {
                "forecast_role_id": self.product_id.forecast_role_id.id,
                "forecast_date_planned_end": self.forecast_date_end,
                "forecast_date_planned_start": self.forecast_date_start,
            }
        )
        return values

    def _timesheet_create_project(self):
        project = super()._timesheet_create_project()
        if self.product_id.project_template_id and self.product_id.forecast_role_id:
            project.tasks.write(
                {
                    "forecast_role_id": self.product_id.forecast_role_id.id,
                    "date_end": self.forecast_date_end,
                    "date_planned_start": self.forecast_date_start,
                }
            )
        return project
