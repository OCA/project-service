# Copyright 2018-2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    assignment_ids = fields.One2many(
        string="Project Assignments",
        comodel_name="project.assignment",
        inverse_name="project_id",
        tracking=True,
    )
    inherit_assignments = fields.Boolean(
        default=lambda self: self._default_inherit_assignments(),
    )
    limit_role_to_assignments = fields.Boolean(
        default=lambda self: self._default_limit_role_to_assignments(),
    )

    @api.model
    def _default_inherit_assignments(self):
        company = self.env["res.company"].browse(
            self._context.get("company_id", self.env.user.company_id.id)
        )
        return company.project_inherit_assignments

    @api.model
    def _default_limit_role_to_assignments(self):
        company = self.env["res.company"].browse(
            self._context.get("company_id", self.env.user.company_id.id)
        )
        return company.project_limit_role_to_assignments

    def _project_role_create_assignment_values(self, vals_list):
        """Complete values with default assignments from company"""
        company_ids = [v["company_id"] for v in vals_list if v.get("company_id")]
        companies = self.env["res.company"].browse(company_ids)
        for values in vals_list:
            company = None
            if values.get("company_id"):
                company = companies.filtered(
                    lambda c, v=values: c.id == v["company_id"]
                )
            if company and "inherit_assignments" not in values:
                values["inherit_assignments"] = company.project_inherit_assignments

            if company and "limit_role_to_assignments" not in values:
                values[
                    "limit_role_to_assignments"
                ] = company.project_limit_role_to_assignments
        return vals_list

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = self._project_role_create_assignment_values(vals_list)
        return super().create(vals_list)
