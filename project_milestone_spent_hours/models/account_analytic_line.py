# Copyright 2024-today Numigi and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    milestone_id = fields.Many2one(
        "project.milestone",
        related="task_id.milestone_id",
        string="Milestone",
        index=True,
        compute_sudo=True,
        store=True,
    )
