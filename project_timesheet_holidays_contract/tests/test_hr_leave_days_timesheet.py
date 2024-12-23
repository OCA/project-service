# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo.tests import RecordCapturer

from .common import ProjectTimesheetHolidaysContractCommon


class TestHRLeaveDaysTimesheet(ProjectTimesheetHolidaysContractCommon):
    @freeze_time("2021-06-01 08:00:00")
    def test_get_duration_for_closed_contract(self):
        # We plan the leaves for the John Doe employee with a 35 hours contract
        # starting from Tuesday/2021-06-01 and ending in 5 days
        # so the working days due to 35 hours contract are:
        # Tuesday (7.75 hours), Wednesday (4 hours),
        # Thursday (7.75 hours), Friday (7.75 hours)
        # attendance days = 4 days and 27.25 hours
        date_start = date.today()
        date_end = date_start + relativedelta(days=5)
        leave = self.env["hr.leave"].create(
            {
                "name": "Test Closed contract",
                "holiday_status_id": self.leave_type.id,
                "request_date_from": date_start,
                "request_date_to": date_end,
                "employee_id": self.employee.id,
            }
        )
        employee = self.employee.with_context(date_to=leave.date_to)
        resource_calendar = employee._get_calendar(leave.date_from)
        days, hours = leave._get_duration(resource_calendar=resource_calendar)
        attended_nb_days = (4, 27.25)
        # 4 days and 27.25 hours should be returned
        self.assertEqual((days, hours), attended_nb_days)

    @freeze_time("2022-06-01 08:00:00")
    def test_get_duration_for_opened_contract(self):
        # We plan the leaves for the John Doe employee with a 40 hours contract
        # starting from Tuesday/2021-06-01 and ending in 5 days
        # so the working days due to 40 hours contract are:
        # Tuesday (8 hours), Wednesday (8 hours),
        # Thursday (8 hours), Friday (8 hours)
        # attendance days = 4 days and 32 hours
        date_start = date.today()
        date_end = date_start + relativedelta(days=5)
        leave = self.env["hr.leave"].create(
            {
                "name": "Test Opened contract",
                "holiday_status_id": self.leave_type.id,
                "request_date_from": date_start,
                "request_date_to": date_end,
                "employee_id": self.employee.id,
            }
        )
        employee = self.employee.with_context(date_to=leave.date_to)
        resource_calendar = employee._get_calendar(leave.date_from)
        days, hours = leave._get_duration(resource_calendar=resource_calendar)
        attended_nb_days = (4.0, 32.0)
        # 4 days and 32 hours should be returned
        self.assertEqual((days, hours), attended_nb_days)

    @freeze_time("2021-06-01 08:00:00")
    def test_timesheet_create_lines_for_closed_contract(self):
        date_start = date.today()
        date_end = date_start + relativedelta(days=5)
        with RecordCapturer(self.env["account.analytic.line"], []) as capture:
            self.env["hr.leave"].create(
                {
                    "name": "Test Closed contract",
                    "holiday_status_id": self.leave_type.id,
                    "request_date_from": date_start,
                    "request_date_to": date_end,
                    "employee_id": self.employee.id,
                }
            )

        timesheets = capture.records
        self.assertEqual(len(timesheets), 4)

    @freeze_time("2022-06-01 08:00:00")
    def test_timesheet_create_lines_for_opened_contract(self):
        date_start = date.today()
        date_end = date_start + relativedelta(days=5)
        with RecordCapturer(self.env["account.analytic.line"], []) as capture:
            self.env["hr.leave"].create(
                {
                    "name": "Test Opened contract",
                    "holiday_status_id": self.leave_type.id,
                    "request_date_from": date_start,
                    "request_date_to": date_end,
                    "employee_id": self.employee.id,
                }
            )

        timesheets = capture.records
        self.assertEqual(len(timesheets), 4)
