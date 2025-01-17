# Copyright 2015 Incaser Informatica S.L. - Sergio Teruel
# Copyright 2015 Incaser Informatica S.L. - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.base.tests.common import BaseCommon


class TestProjectCaseDefault(BaseCommon):
    # Use case : Prepare some data for current test case
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create({"name": "Project Test"})

    def test_project_new(self):
        self.assertEqual(len(self.project.type_ids), 7)
