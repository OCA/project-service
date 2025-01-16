# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

# See _map_tasks_default_valeus
TASK_DEFAULT_COPY_CONTEXT_KEY = f"{__name__}.task_default_copy_context_key"


class Project(models.Model):
    _inherit = "project.project"

    is_template = fields.Boolean(copy=False)

    # CREATE A PROJECT FROM A TEMPLATE AND OPEN THE NEWLY CREATED PROJECT
    def create_project_from_template(self):
        if " (TEMPLATE)" in self.name:
            new_name = self.name.replace(" (TEMPLATE)", " (COPY)")
        else:
            new_name = self.name + " (COPY)"
        new_project = self.with_context(**{TASK_DEFAULT_COPY_CONTEXT_KEY: True}).copy(
            default={"name": new_name, "active": True, "alias_name": False}
        )

        # OPEN THE NEWLY CREATED PROJECT FORM
        return {
            "view_type": "form",
            "view_mode": "form",
            "res_model": "project.project",
            "target": "current",
            "res_id": new_project.id,
            "type": "ir.actions.act_window",
        }

    @api.model
    def _map_tasks_default_valeus(self, task, project):
        defaults = super()._map_tasks_default_valeus(task, project)
        if self.env.context.get(TASK_DEFAULT_COPY_CONTEXT_KEY):
            # date_end normally is not copied on tasks when a project is
            # copied, but we want it when generating from template
            defaults["date_end"] = task.date_end
        return defaults

    # ADD "(TEMPLATE)" TO THE NAME WHEN PROJECT IS MARKED AS A TEMPLATE
    @api.onchange("is_template")
    def on_change_is_template(self):
        # Add "(TEMPLATE)" to the Name if is_template == true
        # if self.name is needed for creating projects via configuration menu
        if self.name:
            if self.is_template:
                if "(TEMPLATE)" not in self.name:
                    self.name = self.name + " (TEMPLATE)"
                if self.user_id:
                    self.user_id = False
                if self.partner_id:
                    self.partner_id = False
                if self.alias_name:
                    self.alias_name = False

            else:
                if " (TEMPLATE)" in self.name:
                    self.name = self.name.replace(" (TEMPLATE)", "")
