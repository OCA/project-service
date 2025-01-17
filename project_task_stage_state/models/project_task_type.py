# Copyright 2014 Daniel Reis
# Copyright 2024 Tecnativa - Víctor Matínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ProjectTaskType(models.Model):
    """Added state in the Project Task Type."""

    _inherit = "project.task.type"

    def _get_task_states(self):
        return self.env["project.task"].fields_get(allfields=["state"])["state"][
            "selection"
        ]

    task_state = fields.Selection(selection="_get_task_states")
