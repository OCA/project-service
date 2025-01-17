# Copyright 2024-today Numigi and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectMilestone(models.Model):
    _inherit = "project.milestone"

    active = fields.Boolean("Active", default=True)
    total_hours = fields.Float(
        compute="_compute_total_hours",
        string="Total Hours",
        compute_sudo=True,
        store=True,
    )

    def write(self, vals):
        res = super(ProjectMilestone, self).write(vals)
        if "project_id" in vals:
            self._remove_task_milestones(vals["project_id"])
        return res

    def _remove_task_milestones(self, project_id):
        self.with_context(active_test=False).mapped("project_task_ids").filtered(
            lambda milestone: not project_id or milestone.project_id.id != project_id
        ).write({"milestone_id": False})

    @api.depends(
        "project_task_ids",
        "project_task_ids.active",
        "project_task_ids.milestone_id",
        "project_task_ids.timesheet_ids",
        "project_task_ids.timesheet_ids.unit_amount",
        "active",
    )
    def _compute_total_hours(self):
        for record in self:
            total_hours = 0.0
            if record.active:
                total_hours = sum(
                    record.project_task_ids.filtered(lambda milestone: milestone.active)
                    .mapped("timesheet_ids")
                    .mapped("unit_amount")
                )
            record.total_hours = total_hours
