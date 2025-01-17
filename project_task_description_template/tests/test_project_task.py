from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProjectTask(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a description template
        self.description_template = self.env[
            "project.task.description.template"
        ].create({"name": "Test Template", "description": "Template Content"})

        # Create a project
        self.project = self.env["project.project"].create({"name": "Test Project"})

    def test_description_template_empty_description(self):
        """Test template addition when task has no initial description"""
        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task"
        task_form.project_id = self.project

        # Initial description is empty
        self.assertFalse(task_form.description)

        # Set the template
        task_form.description_template_id = self.description_template

        # Check if template content was added (as HTML)
        self.assertEqual(task_form.description, "<p>Template Content</p>")

    def test_description_template_existing_description(self):
        """Test template addition when task has existing description"""
        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task"
        task_form.project_id = self.project
        task_form.description = "<p>Existing Content</p>"

        # Verify initial description
        self.assertEqual(task_form.description, "<p>Existing Content</p>")

        # Set the template
        task_form.description_template_id = self.description_template

        # Check if template content was appended to existing description
        self.assertEqual(
            task_form.description, "<p>Existing Content</p><p>Template Content</p>"
        )

    def test_description_template_multiple_changes(self):
        """Test multiple template changes on the same task"""
        # Create a second template
        second_template = self.env["project.task.description.template"].create(
            {"name": "Second Template", "description": "Second Content"}
        )

        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task"
        task_form.project_id = self.project
        task_form.description = "<p>Initial Content</p>"

        # Add first template
        task_form.description_template_id = self.description_template
        self.assertEqual(
            task_form.description, "<p>Initial Content</p><p>Template Content</p>"
        )

        # Add second template
        task_form.description_template_id = second_template
        self.assertEqual(
            task_form.description,
            "<p>Initial Content</p><p>Template Content</p><p>Second Content</p>",
        )

    def test_description_template_null(self):
        """Test behavior when template is cleared"""
        task_form = Form(self.env["project.task"])
        task_form.name = "Test Task"
        task_form.project_id = self.project
        task_form.description = "<p>Initial Content</p>"

        # Set and then clear template
        task_form.description_template_id = self.description_template
        task_form.description_template_id = self.env[
            "project.task.description.template"
        ]

        # Description should remain unchanged after clearing template
        self.assertEqual(
            task_form.description, "<p>Initial Content</p><p>Template Content</p>"
        )
