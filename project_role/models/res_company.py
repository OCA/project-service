# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    project_inherit_assignments = fields.Boolean(
        string="Projects Inherit Assignments",
        default=True,
    )
    project_limit_role_to_assignments = fields.Boolean(
        string="Limit Project Role to Assignments",
        default=False,
    )
