# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ForecastLineModelMixin(models.Model):
    _name = "forecast.line.mixin"
    _description = "mixin for models which generate forecast lines"

    def _get_forecast_lines(self, domain=None):
        self.ensure_one()
        base_domain = [("res_model", "=", self._name), ("res_id", "=", self.id)]
        if domain is not None:
            base_domain += domain
        return self.env["forecast.line"].search(base_domain)
