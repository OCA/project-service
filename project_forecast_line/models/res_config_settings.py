# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    forecast_line_granularity = fields.Selection(
        related="company_id.forecast_line_granularity", readonly=False
    )
    forecast_line_horizon = fields.Integer(
        related="company_id.forecast_line_horizon", readonly=False
    )

    group_forecast_line_on_quotation = fields.Boolean(
        "Forecast Line on Quotations",
        implied_group="project_forecast_line.group_forecast_line_on_quotation",
    )
