# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ForecastRole(models.Model):
    _name = "forecast.role"
    _description = "Employee role for task matching"

    name = fields.Char(required=True)
    description = fields.Text()
