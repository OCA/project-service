# Copyright 2017 Specialty Medical Drugstore
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestProjectTaskPullRequest(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        project_obj = cls.env["project.project"]
        task_obj = cls.env["project.task"]
        cls.new_stage = cls.env.ref("project.project_stage_0")
        cls.inprogress_stage = cls.env.ref("project.project_stage_1")
        cls.done_stage = cls.env.ref("project.project_stage_2")
        cls.cancel_stage = cls.env.ref("project.project_stage_3")
        cls.project_1 = project_obj.create(
            {"name": "Test Project 1", "pr_required_states": [(4, cls.done_stage.id)]}
        )
        cls.project_2 = project_obj.create(
            {
                "name": "Test Project 2",
                "pr_required_states": [
                    (4, cls.done_stage.id),
                    (4, cls.inprogress_stage.id),
                ],
            }
        )
        cls.task_1 = task_obj.create(
            {
                "name": "Test Task 1",
                "project_id": cls.project_1.id,
                "pr_uri": False,
                "stage_id": cls.new_stage.id,
            }
        )
        cls.task_2 = task_obj.create(
            {
                "name": "Test Task 2",
                "project_id": cls.project_2.id,
                "pr_uri": False,
                "stage_id": cls.new_stage.id,
            }
        )
        cls.task_3 = task_obj.create(
            {
                "name": "Test Task 3",
                "project_id": cls.project_2.id,
                "pr_uri": "github.com",
                "stage_id": cls.new_stage.id,
            }
        )

    def test_write_allowed_when_allowed(self):
        self.task_1.write({"stage_id": self.inprogress_stage.id})
        self.task_1.invalidate_recordset()
        self.assertEqual(self.inprogress_stage, self.task_1.stage_id)

    def test_write_not_allowed_without_pr(self):
        with self.assertRaises(ValidationError):
            self.task_1.write({"stage_id": self.done_stage.id})

    def test_write_not_allowed_without_pr_multiple_stages(self):
        with self.assertRaises(ValidationError):
            self.task_2.write({"stage_id": self.inprogress_stage.id})

    def test_write_allowed_with_pr(self):
        self.task_3.write({"stage_id": self.done_stage.id})
        self.task_3.invalidate_recordset()
        self.assertEqual(self.done_stage, self.task_3.stage_id)
