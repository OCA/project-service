# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

<<<<<<< HEAD
    forecast_role_id = fields.Many2one("forecast.role", ondelete="restrict")
=======
    forecast_role_id = fields.Many2one("forecast.role")
>>>>>>> [15.0][ADD] project_forecast_line
