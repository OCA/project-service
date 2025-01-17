# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from datetime import date, datetime, timedelta

from odoo import exceptions
from odoo.tests import Form, common
from odoo.tools.float_utils import float_compare


class TestProjectTimesheetTimeControl(common.TransactionCase):
    def setUp(self):
        super().setUp()
        admin = self.browse_ref("base.user_admin")
        # Stop any timer running
        self.env["account.analytic.line"].search(
            [
                ("date_time", "!=", False),
                ("user_id", "=", admin.id),
                ("project_id.allow_timesheets", "=", True),
                ("unit_amount", "=", 0),
            ]
        ).button_end_work()
        admin.groups_id |= self.browse_ref("hr_timesheet.group_hr_timesheet_user")
        self.uid = admin.id
        self.other_employee = self.env["hr.employee"].create({"name": "Somebody else"})
        self.project = self.env["project.project"].create(
            {"name": "Test project", "allow_timesheets": True}
        )
        self.project_without_timesheets = self.env["project.project"].create(
            {"name": "Test project", "allow_timesheets": False}
        )
        self.analytic_account = self.project.account_id
        self.task = self.env["project.task"].create(
            {"name": "Test task", "project_id": self.project.id}
        )
        self.line = self.env["account.analytic.line"].create(
            {
                "date_time": datetime.now() - timedelta(hours=1),
                "task_id": self.task.id,
                "project_id": self.project.id,
                "account_id": self.analytic_account.id,
                "name": "Test line",
            }
        )

    def _create_wizard(self, action, active_record):
        """Create a new hr.timesheet.switch wizard in the specified context.

        :param dict action: Action definition that creates the wizard.
        :param active_record: Record being browsed when creating the wizard.
        """
        self.assertEqual(action["res_model"], "hr.timesheet.switch")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["view_type"], "form")
        wiz_form = Form(
            active_record.env[action["res_model"]].with_context(
                active_id=active_record.id,
                active_ids=active_record.ids,
                active_model=active_record._name,
                **action.get("context", {}),
            )
        )
        return wiz_form.save()

    def test_aal_from_other_employee_no_button(self):
        """Lines from other employees have no resume/stop button."""
        self.line.employee_id = self.other_employee
        self.assertFalse(self.line.show_time_control)

    def test_create_analytic_line(self):
        line = self._create_analytic_line(datetime(2016, 3, 24, 3), tz="EST")
        self.assertEqual(line.date, date(2016, 3, 23))

    def test_create_analytic_line_with_string_datetime(self):
        line = self._create_analytic_line("2016-03-24 03:00:00", tz="EST")
        self.assertEqual(line.date, date(2016, 3, 23))

    def test_write_analytic_line(self):
        line = self._create_analytic_line(datetime.now())
        line.with_context(tz="EST").date_time = "2016-03-24 03:00:00"
        self.assertEqual(line.date, date(2016, 3, 23))

    def test_write_analytic_line_with_string_datetime(self):
        line = self._create_analytic_line(datetime.now())
        line.with_context(tz="EST").date_time = datetime(2016, 3, 24, 3)
        self.assertEqual(line.date, date(2016, 3, 23))

    def _create_analytic_line(self, datetime_, tz=None):
        return (
            self.env["account.analytic.line"]
            .with_context(tz=tz)
            .create(
                {
                    "date_time": datetime_,
                    "project_id": self.project.id,
                    "name": "Test line",
                }
            )
        )

    def test_aal_time_control_flow(self):
        """Test account.analytic.line time controls."""
        # Duration == 0, stop the timer
        self.assertFalse(self.line.unit_amount)
        self.assertEqual(self.line.show_time_control, "stop")
        self.line.button_end_work()
        # Duration > 0, cannot stop it
        self.assertTrue(self.line.unit_amount)
        with self.assertRaises(exceptions.UserError):
            self.line.button_end_work()
        # Open a new running AAL without wizard
        running_timer = self.line.copy({"unit_amount": False})
        # Use resume wizard
        self.line.invalidate_model()
        self.assertEqual(self.line.show_time_control, "resume")
        resume_action = self.line.button_resume_work()
        wizard = self._create_wizard(resume_action, self.line)
        self.assertLessEqual(wizard.date_time, datetime.now())
        self.assertEqual(wizard.analytic_line_id, self.line)
        self.assertEqual(wizard.name, self.line.name)
        self.assertEqual(wizard.project_id, self.line.project_id)
        self.assertEqual(wizard.running_timer_id, running_timer)
        self.assertEqual(wizard.task_id, self.line.task_id)
        # Changing start time changes expected duration
        wizard.date_time = running_timer.date_time + timedelta(minutes=30)
        self.assertEqual(wizard.running_timer_duration, 0.5)
        wizard.date_time = running_timer.date_time + timedelta(hours=2)
        self.assertEqual(wizard.running_timer_duration, 2)
        # Stop old timer, start new one
        new_act = wizard.with_context(show_created_timer=True).action_switch()
        new_line = self.env[new_act["res_model"]].browse(new_act["res_id"])
        self.assertEqual(
            new_line.date_time, running_timer.date_time + timedelta(hours=2)
        )
        self.assertEqual(new_line.employee_id, running_timer.employee_id)
        self.assertEqual(new_line.project_id, running_timer.project_id)
        self.assertEqual(new_line.task_id, running_timer.task_id)
        self.assertEqual(new_line.unit_amount, 0)
        self.assertEqual(running_timer.unit_amount, 2)

    def test_aal_without_start_resume_button(self):
        """If a line has no start date, can only resume it."""
        self.assertEqual(self.line.show_time_control, "stop")
        self.line.date_time = False
        self.line.invalidate_model()
        self.assertEqual(self.line.show_time_control, "resume")

    def test_error_multiple_running_timers(self):
        """If there are multiple running timers, I don't know which to stop."""
        self.line.copy({})
        self.line.copy({})
        self.line.button_end_work()
        resume_action = self.line.button_resume_work()
        with self.assertRaises(exceptions.UserError):
            self._create_wizard(resume_action, self.line)

    def test_project_time_control_flow(self):
        """Test project.project time controls."""
        # Resuming a project will try to find lines without task
        line_without_task = self.line.copy(
            {"task_id": False, "project_id": self.project.id, "name": "No task here"}
        )
        self.assertFalse(line_without_task.unit_amount)
        # Multiple running lines found, no buttons
        self.assertFalse(self.project.show_time_control)
        # Stop line without task, now we see stop button
        line_without_task.button_end_work()
        self.project.invalidate_model()
        self.assertEqual(self.project.show_time_control, "stop")
        self.project.button_end_work()
        # No more running lines, cannot stop again
        with self.assertRaises(exceptions.UserError):
            self.project.button_end_work()
        # All lines stopped, start new one
        self.task.invalidate_model()
        self.project.invalidate_model()
        self.assertEqual(self.project.show_time_control, "start")
        start_action = self.project.button_start_work()
        wizard = self._create_wizard(start_action, self.project)
        self.assertLessEqual(wizard.date_time, datetime.now())
        self.assertEqual(wizard.analytic_line_id.account_id, self.project.account_id)
        self.assertEqual(wizard.name, "No task here")
        self.assertEqual(wizard.project_id, self.project)
        self.assertFalse(wizard.running_timer_id, self.line)
        self.assertFalse(wizard.task_id)
        new_act = wizard.with_context(show_created_timer=True).action_switch()
        new_line = self.env[new_act["res_model"]].browse(new_act["res_id"])
        self.assertEqual(new_line.employee_id, self.env.user.employee_ids)
        self.assertEqual(new_line.project_id, self.project)
        self.assertFalse(new_line.task_id)
        self.assertEqual(new_line.unit_amount, 0)
        self.assertTrue(self.line.unit_amount)
        # Projects without timesheets show no buttons
        self.assertFalse(self.project_without_timesheets.show_time_control)

    def test_task_time_control_flow(self):
        """Test project.task time controls."""
        # Running line found, stop the timer
        self.assertEqual(self.task.show_time_control, "stop")
        self.task.button_end_work()
        # No more running lines, cannot stop again
        with self.assertRaises(exceptions.UserError):
            self.task.button_end_work()
        # All lines stopped, start new one
        self.assertEqual(self.task.show_time_control, "start")
        start_action = self.task.button_start_work()
        wizard = self._create_wizard(start_action, self.task)
        self.assertLessEqual(wizard.date_time, datetime.now())
        self.assertEqual(
            wizard.analytic_line_id.account_id, self.task.project_id.account_id
        )
        self.assertEqual(wizard.name, self.line.name)
        self.assertEqual(wizard.project_id, self.task.project_id)
        self.assertEqual(wizard.task_id, self.task)
        new_act = wizard.with_context(show_created_timer=True).action_switch()
        new_line = self.env[new_act["res_model"]].browse(new_act["res_id"])
        self.assertEqual(new_line.employee_id, self.env.user.employee_ids)
        self.assertEqual(new_line.project_id, self.project)
        self.assertEqual(new_line.task_id, self.task)
        self.assertEqual(new_line.unit_amount, 0)
        self.assertTrue(self.line.unit_amount)

    def test_wizard_standalone(self):
        """Standalone wizard usage works properly."""
        # It detects the running timer
        wizard = self.env["hr.timesheet.switch"].create(
            {"name": "Standalone 1", "project_id": self.project.id}
        )
        self.assertEqual(wizard.running_timer_id, self.line)
        self.assertTrue(wizard.running_timer_duration)
        new_act = wizard.with_context(show_created_timer=True).action_switch()
        new_line = self.env[new_act["res_model"]].browse(new_act["res_id"])
        self.assertEqual(new_line.name, "Standalone 1")
        self.assertEqual(new_line.project_id, self.project)
        # It also works if there is no running timer
        new_line.button_end_work()
        wizard = (
            self.env["hr.timesheet.switch"]
            .with_context(active_model="unknown", active_id=1)
            .create({"name": "Standalone 2", "project_id": self.project.id})
        )
        self.assertFalse(wizard.running_timer_id)
        self.assertFalse(wizard.running_timer_duration)
        wizard.action_switch()
        new_line = self.env["account.analytic.line"].search(
            [
                ("name", "=", "Standalone 2"),
                ("project_id", "=", self.project.id),
                ("unit_amount", "=", 0),
                ("employee_id", "=", self.line.employee_id.id),
            ]
        )
        self.assertEqual(len(new_line), 1)

    def test_start_end_time(self):
        line = self.line.copy(
            {"task_id": False, "project_id": self.project.id, "name": "No task here"}
        )
        line.date_time = datetime(2020, 8, 1, 10, 0, 0)
        line.unit_amount = 2.0
        self.assertTrue(line.date_time_end == datetime(2020, 8, 1, 12, 0, 0))
        line.date_time_end = datetime(2020, 8, 1, 15, 0, 0)
        self.assertFalse(float_compare(line.unit_amount, 5.0, precision_digits=2))

    def test_non_timesheet_analytic_line(self):
        line = self.env["account.analytic.line"].create(
            {
                "project_id": self.project.id,
                "account_id": self.analytic_account.id,
                "name": "Test non-timesheet line",
                "product_uom_id": self.env.ref("uom.product_uom_gram").id,
            }
        )
        line.unit_amount = 500.0
        self.assertFalse(line.date_time_end)
