# Copyright 2021 - Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    timesheet_ids = fields.One2many(
        domain=[("product_id", "=", None)],
    )
