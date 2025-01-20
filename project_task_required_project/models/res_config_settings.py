# Copyright 2025 Ángel García de la Chica Herrera <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_project_required = fields.Boolean(
        related="company_id.is_project_required",
        store=True,
        readonly=False,
        string="Project Required",
    )
