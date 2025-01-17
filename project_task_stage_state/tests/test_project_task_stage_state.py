from odoo.addons.base.tests.common import BaseCommon


class TestProjectTaskStageState(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stage_new = cls.env.ref("project.project_stage_0")
        cls.stage_in_progress = cls.env.ref("project.project_stage_1")
        cls.stage_done = cls.env.ref("project.project_stage_2")
        cls.stage_canceled = cls.env.ref("project.project_stage_3")

        # Set the task_state explicitly in the stages for proper testing
        cls.stage_in_progress.write({"task_state": "01_in_progress"})
        cls.stage_done.write({"task_state": "1_done"})
        cls.stage_canceled.write({"task_state": "1_canceled"})

        cls.task = cls.env["project.task"].create(
            {
                "name": "Test task",
                "project_id": cls.env.ref("project.project_project_1").id,
                "stage_id": cls.stage_new.id,
                "state": "01_in_progress",
            }
        )

    def test_task_state_is_set_when_stage_has_task_state(self):
        # Test: Change to done, the state should update to "1_done"
        self.task.write({"stage_id": self.stage_done.id})
        self.assertEqual(self.task.state, "1_done")

        # Test: Change to canceled, the state should update to "1_canceled"
        self.task.write({"stage_id": self.stage_canceled.id})
        self.assertEqual(self.task.state, "1_canceled")

        # Test: Change to in progress, the state should update to "01_in_progress"
        self.task.write({"stage_id": self.stage_in_progress.id})
        self.assertEqual(self.task.state, "01_in_progress")

    def test_task_states_dynamic_selection(self):
        # Test: Ensure the task_state field dynamically fetches the correct selection
        expected_states = dict(
            self.env["project.task"].fields_get(allfields=["state"])["state"][
                "selection"
            ]
        )
        self.assertIn(self.stage_done.task_state, expected_states)
        self.assertIn(self.stage_in_progress.task_state, expected_states)
        self.assertIn(self.stage_canceled.task_state, expected_states)

    def test_get_task_states(self):
        # Test: Ensure _get_task_states fetches the correct states dynamically
        task_states = self.stage_done._get_task_states()  # Returns a list of tuples
        expected_states = dict(
            self.env["project.task"].fields_get(allfields=["state"])["state"][
                "selection"
            ]
        )  # Dictionary of expected states

        # Assert that all keys from task_states exist in expected_states
        task_state_keys = [key for key, _ in task_states]
        self.assertEqual(len(task_state_keys), len(expected_states))
        for state_key in task_state_keys:
            self.assertIn(state_key, expected_states)

    def test_task_state_is_none(self):
        # Test: Ensure task_state can be None and doesn't alter the task state
        self.stage_in_progress.write({"task_state": None})
        self.task.write({"stage_id": self.stage_in_progress.id})
        self.assertEqual(self.task.state, "01_in_progress")  # No change expected

    def test_get_task_states_edge_cases(self):
        # Temporarily override the 'state' field's selection
        original_selection = self.env["project.task"]._fields["state"].selection
        try:
            # Set a custom selection for testing edge cases
            self.env["project.task"]._fields["state"].selection = [
                ("edge_case_1", "Edge Case 1"),
                ("edge_case_2", "Edge Case 2"),
            ]

            # Call _get_task_states and validate it includes the edge cases
            task_states = self.stage_done._get_task_states()
            self.assertIn(("edge_case_1", "Edge Case 1"), task_states)
            self.assertIn(("edge_case_2", "Edge Case 2"), task_states)
        finally:
            # Restore the original selection after the test
            self.env["project.task"]._fields["state"].selection = original_selection
