# Copyright 2024 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProjectRequiredFieldByStage(TransactionCase):
    def setUp(self):
        super().setUp()

        self.project_project_model = self.env["project.project"]
        self.project_task_type_model = self.env["project.task.type"]
        self.project_task_model = self.env["project.task"]
        self.res_users_model = self.env["res.users"]
        self.project_project_1 = self.project_project_model.create(
            {
                "name": "Project 1",
            }
        )
        self.project_task_type_1 = self.project_task_type_model.create(
            {
                "name": "Project Stage 1",
                "project_ids": [(4, self.project_project_1.id)],
            }
        )
        self.project_task_type_2 = self.project_task_type_model.create(
            {
                "name": "Project Stage 2",
                "required_field_ids": [
                    (4, self.env.ref("project.field_project_task__user_ids").id)
                ],
                "project_ids": [(4, self.project_project_1.id)],
            }
        )

        self.project_task_1 = self.project_task_model.create(
            {
                "name": "Project Task 1",
                "project_id": self.project_project_1.id,
                "user_ids": False,
                "stage_id": self.project_task_type_1.id,
            }
        )
        self.res_users_1 = self.res_users_model.create(
            {
                "name": "User 1",
                "login": "user@example.com",
                "email": "user@example.com",
                "active": True,
            }
        )

    def test_locking(self):
        with self.assertRaises(UserError):
            self.project_task_1.write(
                {
                    "stage_id": self.project_task_type_2.id,
                }
            )
        self.project_task_1.write(
            {
                "user_ids": [(4, self.res_users_1.id)],
            }
        )
        self.project_task_1.write(
            {
                "stage_id": self.project_task_type_2.id,
            }
        )
        self.assertEqual(self.project_task_1.stage_id.id, self.project_task_type_2.id)

    def test_get_view_required_fields(self):
        arch, view = self.project_task_1._get_view(view_type="form")
        node = arch.xpath("//field[@name='user_ids']")
        self.assertTrue(node)
        attrs = ast.literal_eval(node[0].attrib.get("attrs", "{}"))
        self.assertIn("required", attrs)
        self.assertIn(self.project_task_type_2.id, attrs["required"][0][2])
