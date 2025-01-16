# Copyright 2021 Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestProject(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env.ref("project.project_project_1")
        cls.project.name = "Test project name"
        cls.project.analytic_account_id = cls.env["account.analytic.account"].create(
            {"name": "Test Analytic account name", "code": "Test Weird code"}
        )

    def test_search_project_by_account_analytic_code(self):
        result = self.env["project.project"].name_search(
            name=self.project.analytic_account_id.code
        )
        self.assertEqual(
            result[0][1],
            f"[{self.project.analytic_account_id.code}] {self.project.name}",
        )
