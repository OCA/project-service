# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import api, fields, models

TASK_URL = "/web#id=%s&view_type=form&model=project.task&action=%s"


class Task(models.Model):
    _inherit = "project.task"
    _rec_names_search = ["key", "name"]

    key = fields.Char(size=20, index=True)

    url = fields.Char(string="URL", compute="_compute_task_url")

    _sql_constraints = [("task_key_unique", "UNIQUE(key)", "Task key must be unique!")]

    def _compute_task_url(self):
        action_id = self.env.ref("project.action_view_task").id
        for task in self:
            task.url = TASK_URL % (task.id, action_id)

    @api.model_create_multi
    def create(self, vals_list):
        ctx = self.env.context.get
        for vals in vals_list:
            project_id = vals.get("project_id", False)
            if not project_id:
                project_id = ctx("default_project_id", False)

            if not project_id and ctx("active_model", False) == "project.project":
                project_id = ctx("id", False)

            if project_id:
                project = self.env["project.project"].browse(project_id)
                vals["key"] = project.get_next_task_key()
        return super().create(vals_list)

    def write(self, vals):
        project_id = vals.get("project_id", False)
        if not project_id:
            return super().write(vals)

        project = self.env["project.project"].browse(project_id)
        for task in self:
            if task.key and task.project_id.id == project.id:
                continue

            values = self.prepare_task_for_project_switch(task, project)
            super(Task, task).write(values)

        return super().write(vals)

    def prepare_task_for_project_switch(self, task, project):
        data = {"key": project.get_next_task_key(), "project_id": project.id}

        if len(task.child_ids) > 0:
            data["child_ids"] = [
                (1, child.id, self.prepare_task_for_project_switch(child, project))
                for child in task.child_ids
            ]
        return data

    @api.depends("key", "name")
    def _compute_display_name(self):
        for task in self:
            task_name = []
            if task.key:
                task_name.append(task.key)
            task_name.append(task.name)
            task.display_name = " - ".join(task_name)
