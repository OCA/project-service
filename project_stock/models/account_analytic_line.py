# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    stock_task_id = fields.Many2one(
        comodel_name="project.task", string="Project Task", ondelete="cascade"
    )

    def _timesheet_postprocess_values(self, values):
        """When hr_timesheet addon is installed, in the create() and write() methods,
        the amount is recalculated according to the employee cost.
        We need to force that in the records related to stock tasks the price is not
        updated."""
        res = super()._timesheet_postprocess_values(values)
        for key in self.filtered(lambda x: x.stock_task_id).ids:
            res[key].pop("amount", None)
        return res
