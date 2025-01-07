# Copyright 2021 - Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import date

from odoo import _, fields, models
from odoo.osv import expression
from odoo.tools import float_round

from odoo.addons.sale_timesheet.models.project_overview import _to_action_data


class Project(models.Model):
    _inherit = "project.project"

    timesheet_ids = fields.One2many(
        domain=[("product_id", "=", None)],
    )

    consumable_count = fields.Integer(
        compute="_compute_consumable_count",
        help="Number of consumable lines collected.",
    )

    def _compute_consumable_count(self):
        read_group = {
            group["project_id"][0]: group["project_id_count"]
            for group in self.env["account.analytic.line"].read_group(
                [
                    ("project_id", "in", self.ids),
                    ("product_id", "!=", False),
                ],
                ["project_id"],
                ["project_id"],
            )
        }
        for project in self:
            project.consumable_count = read_group.get(project.id, 0)

    def _plan_prepare_values(self):
        """Overwrite to be consumable aware"""
        currency = self.env.company.currency_id
        uom_hour = self.env.ref("uom.product_uom_hour")
        company_uom = self.env.company.timesheet_encode_uom_id
        is_uom_day = company_uom == self.env.ref("uom.product_uom_day")
        hour_rounding = uom_hour.rounding
        billable_types = [
            "non_billable",
            "non_billable_project",
            "billable_time",
            "non_billable_timesheet",
            "billable_fixed",
        ]

        values = {
            "projects": self,
            "currency": currency,
            "timesheet_domain": [
                ("project_id", "in", self.ids),
                ("product_id", "=", False),
            ],
            "profitability_domain": [("project_id", "in", self.ids)],
            "stat_buttons": self._plan_get_stat_button(),
            "is_uom_day": is_uom_day,
        }

        #
        # Hours, Rates and Profitability
        #
        dashboard_values = {
            "time": dict.fromkeys(billable_types + ["total"], 0.0),
            "rates": dict.fromkeys(billable_types + ["total"], 0.0),
            "profit": {
                "invoiced": 0.0,
                "to_invoice": 0.0,
                "cost": 0.0,
                "total": 0.0,
            },
        }

        # hours from non-invoiced timesheets that are linked to canceled so
        canceled_hours_domain = [
            ("project_id", "in", self.ids),
            ("timesheet_invoice_type", "!=", False),
            ("so_line.state", "=", "cancel"),
            ("product_id", "=", False),
        ]
        total_canceled_hours = sum(
            self.env["account.analytic.line"]
            .search(canceled_hours_domain)
            .mapped("unit_amount")
        )
        canceled_hours = float_round(
            total_canceled_hours, precision_rounding=hour_rounding
        )
        if is_uom_day:
            # convert time from hours to days
            canceled_hours = round(
                uom_hour._compute_quantity(
                    canceled_hours, company_uom, raise_if_failure=False
                ),
                2,
            )
        dashboard_values["time"]["canceled"] = canceled_hours
        dashboard_values["time"]["total"] += canceled_hours

        # hours (from timesheet) and rates (by billable type)
        dashboard_domain = [
            ("project_id", "in", self.ids),
            ("product_id", "=", False),
            ("timesheet_invoice_type", "!=", False),
            "|",
            ("so_line", "=", False),
            ("so_line.state", "!=", "cancel"),
        ]  # force billable type
        dashboard_data = self.env["account.analytic.line"].read_group(
            dashboard_domain,
            ["unit_amount", "timesheet_invoice_type"],
            ["timesheet_invoice_type"],
        )
        dashboard_total_hours = (
            sum([data["unit_amount"] for data in dashboard_data]) + total_canceled_hours
        )
        for data in dashboard_data:
            billable_type = data["timesheet_invoice_type"]
            amount = float_round(
                data.get("unit_amount"), precision_rounding=hour_rounding
            )
            if is_uom_day:
                # convert time from hours to days
                amount = round(
                    uom_hour._compute_quantity(
                        amount, company_uom, raise_if_failure=False
                    ),
                    2,
                )
            dashboard_values["time"][billable_type] = amount
            dashboard_values["time"]["total"] += amount
            # rates
            rate = (
                round(data.get("unit_amount") / dashboard_total_hours * 100, 2)
                if dashboard_total_hours
                else 0.0
            )
            dashboard_values["rates"][billable_type] = rate
            dashboard_values["rates"]["total"] += rate
        dashboard_values["time"]["total"] = round(dashboard_values["time"]["total"], 2)

        # rates from non-invoiced timesheets that are linked to canceled so
        dashboard_values["rates"]["canceled"] = float_round(
            100 * total_canceled_hours / (dashboard_total_hours or 1),
            precision_rounding=hour_rounding,
        )

        # profitability, using profitability SQL report
        field_map = {
            "amount_untaxed_invoiced": "invoiced",
            "amount_untaxed_to_invoice": "to_invoice",
            "timesheet_cost": "cost",
            "consumable_cost": "consumable_cost",
            "expense_cost": "expense_cost",
            "expense_amount_untaxed_invoiced": "expense_amount_untaxed_invoiced",
            "expense_amount_untaxed_to_invoice": "expense_amount_untaxed_to_invoice",
            "other_revenues": "other_revenues",
        }
        profit = dict.fromkeys(
            list(field_map.values()) + ["other_revenues", "total"], 0.0
        )
        profitability_raw_data = self.env["project.profitability.report"].read_group(
            [("project_id", "in", self.ids)],
            ["project_id", "product_id"] + list(field_map),
            ["project_id"],
        )
        for data in profitability_raw_data:
            company_id = (
                self.env["project.project"].browse(data.get("project_id")[0]).company_id
            )
            from_currency = company_id.currency_id
            for field in field_map:
                value = data.get(field, 0.0)
                if from_currency != currency:
                    value = from_currency._convert(
                        value, currency, company_id, date.today()
                    )
                profit[field_map[field]] += value
        profit["total"] = sum([profit[item] for item in profit.keys()])
        dashboard_values["profit"] = profit

        values["dashboard"] = dashboard_values

        #
        # Time Repartition (per employee per billable types)
        #
        employee_ids = self._plan_get_employee_ids()
        employee_ids = list(set(employee_ids))
        # Retrieve the employees for which the current user can see theirs timesheets
        employee_domain = expression.AND(
            [
                [("company_id", "in", self.env.companies.ids)],
                self.env["account.analytic.line"]._domain_employee_id(),
            ]
        )
        employees = (
            self.env["hr.employee"]
            .sudo()
            .browse(employee_ids)
            .filtered_domain(employee_domain)
        )
        repartition_domain = [
            ("project_id", "in", self.ids),
            ("product_id", "=", False),
            ("employee_id", "!=", False),
            ("timesheet_invoice_type", "!=", False),
        ]  # force billable type
        # repartition data, without timesheet on cancelled so
        repartition_data = self.env["account.analytic.line"].read_group(
            repartition_domain
            + ["|", ("so_line", "=", False), ("so_line.state", "!=", "cancel")],
            ["employee_id", "timesheet_invoice_type", "unit_amount"],
            ["employee_id", "timesheet_invoice_type"],
            lazy=False,
        )
        # read timesheet on cancelled so
        cancelled_so_timesheet = self.env["account.analytic.line"].read_group(
            repartition_domain + [("so_line.state", "=", "cancel")],
            ["employee_id", "unit_amount"],
            ["employee_id"],
            lazy=False,
        )
        repartition_data += [
            {**canceled, "timesheet_invoice_type": "canceled"}
            for canceled in cancelled_so_timesheet
        ]

        # set repartition per type per employee
        repartition_employee = {}
        for employee in employees:
            repartition_employee[employee.id] = dict(
                employee_id=employee.id,
                employee_name=employee.name,
                non_billable_project=0.0,
                non_billable=0.0,
                billable_time=0.0,
                non_billable_timesheet=0.0,
                billable_fixed=0.0,
                canceled=0.0,
                total=0.0,
            )
        for data in repartition_data:
            employee_id = data["employee_id"][0]
            repartition_employee.setdefault(
                employee_id,
                dict(
                    employee_id=data["employee_id"][0],
                    employee_name=data["employee_id"][1],
                    non_billable_project=0.0,
                    non_billable=0.0,
                    billable_time=0.0,
                    non_billable_timesheet=0.0,
                    billable_fixed=0.0,
                    canceled=0.0,
                    total=0.0,
                ),
            )[data["timesheet_invoice_type"]] = float_round(
                data.get("unit_amount", 0.0), precision_rounding=hour_rounding
            )
            repartition_employee[employee_id][
                "__domain_" + data["timesheet_invoice_type"]
            ] = data["__domain"]
        # compute total
        for employee_id, vals in repartition_employee.items():
            repartition_employee[employee_id]["total"] = sum(
                [vals[inv_type] for inv_type in [*billable_types, "canceled"]]
            )
            if is_uom_day:
                # convert all times from hours to days
                for time_type in [
                    "non_billable_project",
                    "non_billable",
                    "billable_time",
                    "non_billable_timesheet",
                    "billable_fixed",
                    "canceled",
                    "total",
                ]:
                    if repartition_employee[employee_id][time_type]:
                        repartition_employee[employee_id][time_type] = round(
                            uom_hour._compute_quantity(
                                repartition_employee[employee_id][time_type],
                                company_uom,
                                raise_if_failure=False,
                            ),
                            2,
                        )
        hours_per_employee = [
            repartition_employee[employee_id]["total"]
            for employee_id in repartition_employee
        ]
        values["repartition_employee_max"] = (
            max(hours_per_employee) if hours_per_employee else 1
        ) or 1
        values["repartition_employee"] = repartition_employee

        #
        # Table grouped by SO / SOL / Employees
        #
        timesheet_forecast_table_rows = self._table_get_line_values(employees)
        if timesheet_forecast_table_rows:
            values["timesheet_forecast_table"] = timesheet_forecast_table_rows
        return values

    def _plan_get_stat_button(self):
        """Overlaod to add consumable stat button and alter timesheet button"""
        stat_buttons = super()._plan_get_stat_button()

        stat_buttons.pop()

        ts_tree = self.env.ref(
            "project_consumable.project_consumable_product_line_tree"
        )
        ts_form = self.env.ref(
            "project_consumable.project_consumable_product_line_form"
        )
        stat_buttons.append(
            {
                "name": _("Consumable"),
                "count": sum(self.mapped("consumable_count")),
                "icon": "fa fa-copy",
                "action": _to_action_data(
                    "account.analytic.line",
                    domain=[
                        ("project_id", "in", self.ids),
                        ("product_id", "!=", False),
                    ],
                    views=[(ts_tree.id, "list"), (ts_form.id, "form")],
                ),
            }
        )

        ts_tree = self.env.ref("hr_timesheet.hr_timesheet_line_tree")
        ts_form = self.env.ref("hr_timesheet.hr_timesheet_line_form")
        if self.env.company.timesheet_encode_uom_id == self.env.ref(
            "uom.product_uom_day"
        ):
            timesheet_label = [_("Days"), _("Recorded")]
        else:
            timesheet_label = [_("Hours"), _("Recorded")]
        stat_buttons.append(
            {
                "name": timesheet_label,
                "count": sum(self.mapped("total_timesheet_time")),
                "icon": "fa fa-calendar",
                "action": _to_action_data(
                    "account.analytic.line",
                    domain=[("project_id", "in", self.ids), ("product_id", "=", False)],
                    views=[(ts_tree.id, "list"), (ts_form.id, "form")],
                ),
            }
        )

        return stat_buttons

    def _table_rows_sql_query(self):
        """change the query in order to remove consumable lines"""
        _, query_params = super()._table_rows_sql_query()
        query = """
            SELECT
                'timesheet' AS type,
                date_trunc('month', date)::date AS month_date,
                E.id AS employee_id,
                S.order_id AS sale_order_id,
                A.so_line AS sale_line_id,
                SUM(A.unit_amount) AS number_hours
            FROM account_analytic_line A
                JOIN hr_employee E ON E.id = A.employee_id
                LEFT JOIN sale_order_line S ON S.id = A.so_line
            WHERE A.project_id IS NOT NULL
                AND A.project_id IN %s
                AND A.date < %s
                AND A.product_id IS NULL
            GROUP BY date_trunc('month', date)::date, S.order_id, A.so_line, E.id
        """
        return query, query_params
