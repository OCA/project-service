# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    forecast_line_granularity = fields.Selection(
        [("day", "Day"), ("week", "Week"), ("month", "Month")],
        default="month",
        help="Periodicity of the forecast that will be generated",
    )
    forecast_line_horizon = fields.Integer(
        help="Number of month for the forecast planning", default=12
    )

    def write(self, values):
        res = super().write(values)
        if "forecast_line_granularity" in values or "forecast_line_horizon" in values:
            for company in self:
                self.env["forecast.line"]._cron_recompute_all(
                    force_company_id=company.id, force_delete=True
                )
        return res
