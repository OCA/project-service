# Copyright 2025 Ángel García de la Chica Herrera <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class Task(models.Model):
    _inherit = "project.task"

    @api.constrains("project_id")
    def _check_project_id_not_null(self):
        if self.env.company.is_project_required and any(
            not record.project_id for record in self
        ):
            raise UserError(_("ERROR! A project has not been selected for the task."))
