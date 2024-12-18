from odoo.tests.common import TransactionCase


class TestProjectStageExtraInfo(TransactionCase):
    def setUp(self):
        super().setUp()

        self.stage_to_do = self.env["project.project.stage"].create({"name": "To Do"})
        self.stage_done = self.env["project.project.stage"].create(
            {"name": "Done", "is_closed": True}
        )
        self.project = self.env["project.project"].create({"name": "Project"})

    def test_project_stages(self):
        """Test to verify the behavior of project stages' and is_closed field."""
        self.project.stage_id = self.stage_to_do
        self.assertEqual(
            self.project.stage_id.is_closed,
            False,
            "The project stage 'To Do' should not be marked as closed.",
        )

        self.project.stage_id = self.stage_done
        self.assertEqual(
            self.project.stage_id.is_closed,
            True,
            "The project stage 'Done' should be marked as closed.",
        )
