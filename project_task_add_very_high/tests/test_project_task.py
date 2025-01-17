from odoo.tests.common import TransactionCase


class TestProjectTaskPriority(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project_task_model = self.env["project.task"]

    def test_priority_selection(self):
        """Test that the priority field includes the new options."""
        # Get the priority field definition
        priority_field = self.project_task_model.fields_get(allfields=["priority"])[
            "priority"
        ]

        # Verify the new priority options are included
        expected_options = [("2", "Very High"), ("3", "Most Important")]
        for option in expected_options:
            self.assertIn(
                option,
                priority_field["selection"],
                f"{option} not found in priority selection",
            )

    def test_create_task_with_new_priority(self):
        """Test creating tasks with the new priorities."""
        # Create a task with the new priority "Very High"
        task = self.project_task_model.create(
            {
                "name": "Test Very High Priority Task",
                "priority": "2",
            }
        )
        self.assertEqual(task.priority, "2", "Task priority should be '2' (Very High)")

        # Create a task with the new priority "Most Important"
        task = self.project_task_model.create(
            {
                "name": "Test Most Important Priority Task",
                "priority": "3",
            }
        )
        self.assertEqual(
            task.priority, "3", "Task priority should be '3' (Most Important)"
        )

    def test_update_priority(self):
        """Test updating task priority."""
        # Create a task with a default priority
        task = self.project_task_model.create({"name": "Test Task"})
        self.assertEqual(task.priority, "0", "Default task priority should be '0'")

        # Update the priority to "Very High"
        task.write({"priority": "2"})
        self.assertEqual(
            task.priority, "2", "Task priority should be updated to '2' (Very High)"
        )

        # Update the priority to "Most Important"
        task.write({"priority": "3"})
        self.assertEqual(
            task.priority,
            "3",
            "Task priority should be updated to '3' (Most Important)",
        )

    def test_invalid_priority(self):
        """Test that an invalid priority value raises an error."""
        with self.assertRaises(
            ValueError, msg="Invalid priority should raise ValueError"
        ):
            self.project_task_model.create(
                {"name": "Invalid Priority Task", "priority": "99"}
            )

    def test_priority_mass_update(self):
        """Test mass update of priority from '2' and '3' to '1'."""
        # Create tasks with priorities "2" and "3"
        task_very_high = self.project_task_model.create(
            {"name": "Task Very High", "priority": "2"}
        )
        task_most_important = self.project_task_model.create(
            {"name": "Task Most Important", "priority": "3"}
        )

        # Execute the hook line
        self.env["project.task"].sudo().search([("priority", "in", ["2", "3"])]).write(
            {"priority": "1"}
        )

        # Assert the priorities are updated
        self.assertEqual(
            task_very_high.priority, "1", "Task priority should be updated to '1'"
        )
        self.assertEqual(
            task_most_important.priority, "1", "Task priority should be updated to '1'"
        )
