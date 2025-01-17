# Copyright 2024-today Numigi and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestMilestoneTotalHours(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.project = cls.env["project.project"].create({"name": "My Project"})

        cls.milestone_1 = cls.env["project.milestone"].create(
            {"name": "My Milestone 1", "project_id": cls.project.id}
        )

        cls.milestone_2 = cls.env["project.milestone"].create(
            {"name": "My Milestone 2", "project_id": cls.project.id}
        )

        cls.task = cls.env["project.task"].create(
            {
                "name": "My Task",
                "project_id": cls.project.id,
                "milestone_id": cls.milestone_1.id,
            }
        )

        cls.analytic_line_1 = cls.env["account.analytic.line"].create(
            {
                "name": "My Timesheet 1",
                "task_id": cls.task.id,
                "unit_amount": 10,
                "project_id": cls.project.id,
            }
        )

        cls.analytic_line_2 = cls.env["account.analytic.line"].create(
            {
                "name": "My Timesheet 2",
                "task_id": cls.task.id,
                "unit_amount": 20,
                "project_id": cls.project.id,
            }
        )

    def test_propagate_milestone_on_analytic_line(self):
        assert self.task.milestone_id & self.analytic_line_1.milestone_id

    def test_update_milestone_total_hours_when_creating_analytic_line(self):
        assert self.milestone_1.total_hours == 30

    def test_update_milestone_total_hours_when_updating_analytic_line(self):
        self.analytic_line_1.unit_amount = 20
        assert self.milestone_1.total_hours == 40

    def test_update_milestone_total_hours_when_removing_analytic_line(self):
        self.analytic_line_1.unlink()
        assert self.milestone_1.total_hours == 20

    def test_update_milestone_total_hours_when_modifying_milestone_on_task(self):
        self.task.milestone_id = self.milestone_2
        assert self.milestone_1.total_hours == 0
        assert self.milestone_2.total_hours == 30

    def test_update_milestone_total_hours_when_task_inactive(self):
        self.task.active = 0
        assert self.milestone_1.total_hours == 0
        assert self.milestone_2.total_hours == 0

    def test_update_milestone_total_hours_when_remove_project(self):
        self.milestone_1.project_id = False
        assert self.milestone_1.total_hours == 0
