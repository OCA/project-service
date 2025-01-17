# Copyright 2023 - Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    description_template_id = fields.Many2one(
        "project.task.description.template", store=False
    )

    @api.onchange("description_template_id")
    def _onchange_description_template_id(self):
        if self.description_template_id:
            description = self.description if self.description else ""
            self.description = description + self.description_template_id.description
