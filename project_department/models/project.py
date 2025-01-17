# © 2014 Joël Grand-Guillaume (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    project_department_id = fields.Many2one(
        related="project_id.department_id",
        string="Project Department",
        store=True,
    )


class ProjectProject(models.Model):
    _inherit = "project.project"

    department_id = fields.Many2one(
        comodel_name="hr.department", string="Project Department"
    )
