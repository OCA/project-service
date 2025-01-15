from odoo.tests.common import TransactionCase


class TestProjectRisk(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.project = cls.env["project.project"].create(
            {"name": "Research &amp; Development", "privacy_visibility": "followers"}
        )
        cls.risk_category = cls.env["project.risk.category"].create({"name": "Quality"})
        cls.risk = cls.env["project.risk"].create(
            {
                "name": "Risk X",
                "project_id": cls.project.id,
                "project_risk_category_id": cls.risk_category.id,
                "probability": "2",
                "impact": "2",
            }
        )

    def test_project(self):
        self.assertEqual(self.project.project_risk_count, 1)
        action = self.project.view_risk()
        self.assertEqual(action["context"]["default_project_id"], self.project.id)
        self.assertListEqual(action["domain"], [("project_id", "=", self.project.id)])

    def test_risk(self):
        self.risk.write({"actionee_id": self.env.user.id, "owner_id": self.env.user.id})
        self.assertEqual(self.risk.rating, "4")
