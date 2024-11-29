# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import api, fields, models
from odoo.tools import config


class Project(models.Model):
    _inherit = "project.project"
    _rec_names_search = ["key", "name", "id"]

    task_key_sequence_id = fields.Many2one(
        comodel_name="ir.sequence", string="Key Sequence", ondelete="restrict"
    )

    key = fields.Char(size=10, index=True, copy=False)

    _sql_constraints = [
        ("project_key_unique", "UNIQUE(key)", "Project key must be unique")
    ]

    @api.onchange("name")
    def _onchange_project_name(self):
        for rec in self:
            if rec.key:
                continue

            if rec.name:
                rec.key = self.generate_project_key(rec.name)
            else:
                rec.key = ""

    @api.model_create_multi
    def create(self, vals_list):
        new_projects = self.env["project.project"]
        for vals in vals_list:
            key = vals.get("key", False)
            if not key:
                vals["key"] = self.generate_project_key(vals["name"])

            # Tasks must be created after the project.
            task_vals = vals.pop("task_ids", [])

            new_project = super().create(vals)
            new_projects |= new_project

            # The key sequences to create stories and tasks with keys, created with
            # a project, must be linked to the project company to avoid security
            # issues.
            # Propagate the company ID, using the context key, to fill the
            # sequences company.
            company_id = vals.get("company_id")
            if company_id:
                new_project = new_project.with_context(
                    project_sequence_company=company_id
                )

            new_project.create_sequence()

            # Tasks must be created after the project.
            if task_vals:
                new_project.write({"task_ids": task_vals})

        return new_projects

    def write(self, values):
        update_key = False

        if "key" in values:
            key = values["key"]
            update_key = self.key != key

        res = super().write(values)

        if update_key:
            # Here we don't expect to have more than one record
            # because we can not have multiple projects with the same KEY.
            self.update_sequence()
            self._update_task_keys()

        return res

    def unlink(self):
        for project in self:
            sequence = project.task_key_sequence_id
            project.task_key_sequence_id = False
            sequence.sudo().unlink()
        return super().unlink()

    def create_sequence(self):
        """
        This method creates ir.sequence fot the current project
        :return: Returns create sequence
        """
        self.ensure_one()
        sequence_data = self._prepare_sequence_data()
        sequence = self.env["ir.sequence"].sudo().create(sequence_data)
        self.write({"task_key_sequence_id": sequence.id})
        return sequence

    def update_sequence(self):
        """
        This method updates existing task sequence
        :return:
        """
        sequence_data = self._prepare_sequence_data(init=False)
        self.task_key_sequence_id.sudo().write(sequence_data)

    def _prepare_sequence_data(self, init=True):
        """
        This method prepares data for create/update_sequence methods
        :param init: Set to False in case you don't want to set initial values
        for number_increment and number_next_actual
        """
        values = {
            "name": "{} {}".format(
                self.env._("Project task sequence for project"), self.name
            ),
            "implementation": "standard",
            "code": f"project.task.key.{self.id}",
            "prefix": f"{self.key}-",
            "use_date_range": False,
        }

        # The key sequences to create stories and tasks with keys, created with
        # a project, must be linked to the project company to avoid security
        # issues.
        company_id = self.env.context.get("project_sequence_company")
        if company_id:
            values["company_id"] = company_id

        if init:
            values.update(dict(number_increment=1, number_next_actual=1))

        return values

    def get_next_task_key(self):
        test_project_key = self.env.context.get("test_project_key")
        if (config["test_enable"] and not test_project_key) or (
            config["demo"].get("project_key") and not test_project_key
        ):
            return False
        return self.sudo().task_key_sequence_id.next_by_id()

    def generate_project_key(self, text):
        test_project_key = self.env.context.get("test_project_key")
        if (config["test_enable"] and not test_project_key) or (
            config["demo"].get("project_key") and not test_project_key
        ):
            return False

        if not text:
            return ""

        data = text.split(" ")
        if len(data) == 1:
            return self._generate_project_unique_key(data[0][:3].upper())

        key = []
        for item in data:
            key.append(item[:1].upper())
        return self._generate_project_unique_key("".join(key))

    def _generate_project_unique_key(self, text):
        res = text
        unique_key = False
        counter = 0
        while not unique_key:
            if counter != 0:
                res = f"{text}{counter}"
            unique_key = not bool(self.search([("key", "=", res)]))
            counter += 1

        return res

    def _update_task_keys(self):
        """
        This method will update task keys of the current project.
        """
        self.ensure_one()
        self.flush_model()
        reindex_query = """
        UPDATE project_task
        SET key = x.key
        FROM (
          SELECT t.id, p.key || '-' || split_part(t.key, '-', 2) AS key
          FROM project_task t
          INNER JOIN project_project p ON t.project_id = p.id
          WHERE t.project_id = %s
        ) AS x
        WHERE project_task.id = x.id;
        """

        self.env.cr.execute(reindex_query, (self.id,))
        self.task_ids.invalidate_model(["key"])

    @api.model
    def _set_default_project_key(self):
        """
        This method will be called from the post_init hook in order to set
        default values on project.project and
        project.task, so we leave those tables nice and clean after module
        installation.
        :return:
        """
        for project in self.with_context(active_test=False).search(
            [("key", "=", False)]
        ):
            project.key = self.generate_project_key(project.name)
            project.create_sequence()

            for task in project.task_ids:
                task.key = project.get_next_task_key()
