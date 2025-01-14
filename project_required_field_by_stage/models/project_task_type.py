# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProjectTaskType(models.Model):

    _inherit = "project.task.type"

    required_field_ids = fields.Many2many(
        comodel_name="ir.model.fields",
        domain=[("model", "=", "project.task")],
        help="Fields that are required when the task is in this stage.",
    )
