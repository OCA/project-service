# Copyright 2023 - Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ProjectTaskDescriptionTemplate(models.Model):
    _name = "project.task.description.template"
    _description = "Project Task Description Template"

    name = fields.Char(required=True)
    description = fields.Html(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
