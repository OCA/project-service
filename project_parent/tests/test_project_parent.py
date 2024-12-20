# Copyright 2020 haulogy SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestProjectParent(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project_project_1 = cls.env.ref("project.project_project_1")
        cls.project_project_2 = cls.env.ref("project.project_project_2")
        cls.project_project_3 = cls.env["project.project"].create(
            {"name": "TestProject", "parent_id": cls.project_project_1.id}
        )

    def test_parent_childs_project(self):
        self.assertIn(self.project_project_2, self.project_project_1.child_ids)
        self.assertIn(self.project_project_3, self.project_project_1.child_ids)

    def test_action_open_child_project(self):
        res = self.project_project_1.action_open_child_project()
        self.assertEqual(
            res.get("domain"), [("parent_id", "=", self.project_project_1.id)]
        )
        self.assertEqual(
            res.get("context").get("default_parent_id"), self.project_project_1.id
        )
