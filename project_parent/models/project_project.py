# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Project(models.Model):
    _inherit = "project.project"
    _parent_store = True
    _parent_name = "parent_id"

    parent_id = fields.Many2one(
        comodel_name="project.project", string="Parent Project", index=True
    )
    child_ids = fields.One2many(
        comodel_name="project.project", inverse_name="parent_id", string="Sub-projects"
    )

    parent_path = fields.Char(index="btree")

    child_ids_count = fields.Integer(compute="_compute_child_ids_count", store=True)

    @api.depends("child_ids")
    def _compute_child_ids_count(self):
        for project in self:
            project.child_ids_count = len(project.child_ids)

    def action_open_child_project(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update(default_parent_id=self.id)
        domain = [("parent_id", "=", self.id)]
        return {
            "type": "ir.actions.act_window",
            "view_type": "form",
            "name": f"Children of {self.name}",
            "view_mode": "list,form,graph",
            "res_model": "project.project",
            "target": "current",
            "context": ctx,
            "domain": domain,
        }
