# Copyright 2019 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProjectTask(models.Model):
    _name = "project.task"
    _inherit = ["project.task", "hr.timesheet.time_control.mixin"]

    @api.model
    def _relation_with_timesheet_line(self):
        return "task_id"

    @api.depends(
        "project_id.allow_timesheets",
        "timesheet_ids.employee_id",
        "timesheet_ids.unit_amount",
    )
    def _compute_show_time_control(self):
        result = super()._compute_show_time_control()
        for task in self:
            # Never show button if timesheets are not allowed in project
            if not task.project_id.allow_timesheets:
                task.show_time_control = False
        return result

    def button_start_work(self):
        result = super().button_start_work()
        result["context"].update({"default_project_id": self.project_id.id})
        return result
