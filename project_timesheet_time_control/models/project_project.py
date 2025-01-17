# Copyright 2019 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProjectProject(models.Model):
    _name = "project.project"
    _inherit = ["project.project", "hr.timesheet.time_control.mixin"]

    @api.model
    def _relation_with_timesheet_line(self):
        return "project_id"

    @api.depends("allow_timesheets")
    def _compute_show_time_control(self):
        result = super()._compute_show_time_control()
        for project in self:
            # Never show button if timesheets are not allowed in project
            if not project.allow_timesheets:
                project.show_time_control = False
        return result

    def button_start_work(self):
        result = super().button_start_work()
        # When triggering from project is usually to start timer without task
        result["context"].update({"default_task_id": False})
        return result
