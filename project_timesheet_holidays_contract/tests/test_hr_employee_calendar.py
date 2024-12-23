# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from freezegun import freeze_time

from .common import ProjectTimesheetHolidaysContractCommon


class TestHrEmployeeCalendar(ProjectTimesheetHolidaysContractCommon):
    @freeze_time("2021-06-01 08:00:00")
    def test_get_calendar_from_closed_contract(self):
        date_start = datetime.today()
        date_end = date_start + timedelta(days=5)
        calendar = self.employee.with_context(date_to=date_end)._get_calendar(
            date_start
        )
        self.assertEqual(calendar, self.closed_calendar)

    @freeze_time("2022-06-01 08:00:00")
    def test_get_calendar_from_opened_contract(self):
        date_start = datetime.today()
        date_end = date_start + timedelta(days=5)
        calendar = self.employee.with_context(date_to=date_end)._get_calendar(
            date_start
        )
        self.assertEqual(calendar, self.opened_calendar)
