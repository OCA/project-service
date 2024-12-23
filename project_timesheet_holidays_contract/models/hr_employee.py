# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_calendar(self, date_from=None):
        if not date_from:  # no `date_from` => call `super()`
            return super()._get_calendar(date_from)

        date_from = (
            date_from if not isinstance(date_from, datetime) else date_from.date()
        )
        date_to = self.env.context.get("date_to", None)
        if date_to is None:
            date_to = fields.Date.today()
        date_to = date_to if not isinstance(date_to, datetime) else date_to.date()

        contracts = (
            self.sudo()
            .with_context(active_test=True)
            .env["hr.contract"]
            .search(
                [
                    ("employee_id", "=", self.id),
                    ("date_start", "<=", date_from),
                    "|",
                    ("date_end", ">=", date_to),
                    ("date_end", "=", False),
                ]
            )
        )

        # If only one contract, return it regardless of its state
        if len(contracts) == 1:
            return contracts[0].resource_calendar_id

        # Filter out cancelled contracts if there are multiple contracts
        valid_contracts = contracts.filtered(lambda c: c.state != "cancel")

        # If exactly one non-cancelled contract, return it
        if len(valid_contracts) == 1:
            return valid_contracts[0].resource_calendar_id

        # If there are multiple non-cancelled contracts, raise an error
        if len(valid_contracts) > 1:
            raise ValidationError(_("This period overlaps multiple contracts!"))

        # If no valid contracts remain, call `super()`
        return super()._get_calendar(date_from)

    def _get_work_days_data_batch(
        self,
        from_datetime,
        to_datetime,
        compute_leaves=True,
        calendar=None,
        domain=None,
    ):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Exit early if a calendar is already provided
        if calendar:
            return super()._get_work_days_data_batch(
                from_datetime=from_datetime,
                to_datetime=to_datetime,
                compute_leaves=compute_leaves,
                calendar=calendar,
                domain=domain,
            )

        # Update context on the whole recordset
        self = self.with_context(date_to=to_datetime)

        result = {}
        for employee in self:
            # Retrieve a calendar specific to the employee
            employee_calendar = employee._get_calendar(from_datetime)
            result.update(
                super(HrEmployee, employee)._get_work_days_data_batch(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    compute_leaves=compute_leaves,
                    calendar=employee_calendar,
                    domain=domain,
                )
            )

        return result

    def _get_leave_days_data_batch(
        self, from_datetime, to_datetime, calendar=None, domain=None
    ):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Exit early if a calendar is already provided
        if calendar:
            return super()._get_leave_days_data_batch(
                from_datetime=from_datetime,
                to_datetime=to_datetime,
                calendar=calendar,
                domain=domain,
            )

        # Update context on the whole recordset
        self = self.with_context(date_to=to_datetime)

        result = {}
        for employee in self:
            # Retrieve a calendar specific to the employee
            employee_calendar = employee._get_calendar(from_datetime)
            result.update(
                super(HrEmployee, employee)._get_leave_days_data_batch(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    calendar=employee_calendar,
                    domain=domain,
                )
            )

        return result

    def list_work_time_per_day(
        self, from_datetime, to_datetime, calendar=None, domain=None
    ):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Exit early if a calendar is already provided
        if calendar:
            return super().list_work_time_per_day(
                from_datetime=from_datetime,
                to_datetime=to_datetime,
                calendar=calendar,
                domain=domain,
            )

        # Update context on the whole recordset
        self = self.with_context(date_to=to_datetime)

        result = []
        for employee in self:
            # Retrieve a calendar specific to the employee
            employee_calendar = employee._get_calendar(from_datetime)
            result.extend(
                super(HrEmployee, employee).list_work_time_per_day(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    calendar=employee_calendar,
                    domain=domain,
                )
            )

        return result

    def list_leaves(self, from_datetime, to_datetime, calendar=None, domain=None):
        # OVERRIDE calendar in favor of the one taken from employee's contract
        # Exit early if a calendar is already provided
        if calendar:
            return super().list_leaves(
                from_datetime=from_datetime,
                to_datetime=to_datetime,
                calendar=calendar,
                domain=domain,
            )

        # Update context on the whole recordset
        self = self.with_context(date_to=to_datetime)

        result = []
        for employee in self:
            # Retrieve a calendar specific to the employee
            employee_calendar = employee._get_calendar(from_datetime)
            result.extend(
                super(HrEmployee, employee).list_leaves(
                    from_datetime=from_datetime,
                    to_datetime=to_datetime,
                    calendar=employee_calendar,
                    domain=domain,
                )
            )

        return result
