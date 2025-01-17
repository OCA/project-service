# Copyright 2014 Daniel Reis
# Copyright 2024 Tecnativa - Víctor Matínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    stage_id = fields.Many2one(inverse="_inverse_stage_id")

    def _inverse_stage_id(self):
        for task in self:
            if task.stage_id.task_state and task.stage_id.task_state != task.state:
                task.state = task.stage_id.task_state
