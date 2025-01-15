# Copyright 2019 Onestein
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProjectRiskResponse(models.Model):
    _name = "project.risk.response"
    _description = "Project Risks Responses"

    project_risk_id = fields.Many2one(comodel_name="project.risk")

    sequence = fields.Integer()

    description = fields.Char()
