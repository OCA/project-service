# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import Command
from odoo.tests import common

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class ProjectTimesheetHolidaysContractCommon(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        # Creates 1 test company and a calendar for employees that
        # work part time. Then creates an employee per calendar (one
        # for the standard calendar and one for the one we created)
        cls.test_company = cls.env["res.company"].create(
            {
                "name": "My Test Company",
            }
        )

        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Paid Time Off",
                "time_type": "leave",
                "leave_validation_type": "no_validation",
                "requires_allocation": "no",
                "timesheet_task_id": cls.test_company.leave_timesheet_task_id.id,
                "company_id": cls.test_company.id,
            }
        )
        cls.opened_calendar = cls._define_calendar(
            "40 Hours",
            [
                (8, 12, 0),  # Monday
                (14, 18, 0),  # Monday
                (8, 12, 1),  # Tuesday
                (14, 18, 1),  # Tuesday
                (8, 12, 2),  # Wednesday
                (14, 18, 2),  # Wednesday
                (8, 12, 3),  # Thursday
                (14, 18, 3),  # Thursday
                (8, 12, 4),  # Friday
                (14, 18, 4),  # Friday
            ],
            "UTC",
        )
        cls.closed_calendar = cls._define_calendar(
            "35 Hours",
            [
                (8, 12, 0),  # Monday
                (14, 17.75, 0),  # Monday
                (8, 12, 1),  # Tuesday
                (14, 17.75, 1),  # Tuesday
                (8, 12, 2),  # Wednesday
                (8, 12, 3),  # Thursday
                (14, 17.75, 3),  # Thursday
                (8, 12, 4),  # Friday
                (14, 17.75, 4),  # Friday
            ],
            "UTC",
        )

        # We define the last contract's calendar by defaults for the employee
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "John Doe",
                "company_id": cls.test_company.id,
                "resource_calendar_id": cls.opened_calendar.id,
            }
        )
        cls.current_contract = cls.create_contract(
            cls.employee, cls.opened_calendar, datetime(2022, 1, 1).date()
        )
        cls.close_contract = cls.create_contract(
            cls.employee,
            cls.closed_calendar,
            datetime(2021, 1, 1).date(),
            datetime(2021, 12, 31).date(),
        )

    @classmethod
    def create_contract(cls, employee, calendar, start, end=None):
        return cls.env["hr.contract"].create(
            {
                "name": calendar.name,
                "employee_id": employee.id,
                "state": "close" if end else "open",
                "kanban_state": "normal",
                "wage": 1,
                "date_start": start,
                "date_end": end,
                "resource_calendar_id": calendar.id,
            }
        )

    @classmethod
    def _define_calendar(cls, name, attendances, tz):
        return cls.env["resource.calendar"].create(
            {
                "name": name,
                "tz": tz,
                "attendance_ids": [
                    (
                        Command.create(
                            {
                                "name": "%s_%d" % (name, index),
                                "hour_from": att[0],
                                "hour_to": att[1],
                                "dayofweek": str(att[2]),
                            },
                        )
                    )
                    for index, att in enumerate(attendances)
                ],
            }
        )
