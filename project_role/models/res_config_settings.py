# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    project_inherit_assignments = fields.Boolean(
        related="company_id.project_inherit_assignments",
        readonly=False,
    )
    project_limit_role_to_assignments = fields.Boolean(
        related="company_id.project_limit_role_to_assignments",
        readonly=False,
    )
