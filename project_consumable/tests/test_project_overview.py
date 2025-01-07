# Copyright 2021 - Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tools import float_compare, float_is_zero

from odoo.addons.sale_timesheet.tests.common_reporting import TestCommonReporting


@tagged("-at_install", "post_install")
class TestSaleProject(TestCommonReporting):
    """Mainly inspired from odoo.addons.sale_timesheet.tests.test_project_overview
    adding consumable
    """

    def setUp(self):
        super().setUp()
        self.product_consumable = self.env.ref(
            "project_consumable.product_coffee_capsule"
        )
        self.product_consumable.standard_price = 13

    def _long_consumable_user(self, project, quantity, task=None, **kwargs):
        data = {
            "name": "collect test material",
            "project_id": project.id,
            "account_id": None,  # automatically set
            "product_id": self.product_consumable.id,
            "unit_amount": quantity,
            # "employee_id": self.employee.id,
            "product_uom_id": None,  # Should be set if not provided
            "task_id": task.id if task else None,
            "employee_id": self.employee_user.id,
            "amount": None,  # Should be computed
            "date": None,  # Default should be today
            "partner_id": None,  # no require here
        }
        data.update(**kwargs)
        data = {k: v for k, v in data.items() if v is not None}

        return self.env["account.analytic.line"].create(data)

    def test_project_overview_by_project(self):
        rounding = self.env.company.currency_id.rounding

        so_line_deliver_global_project = self.env["sale.order.line"].create(
            {
                "name": self.product_delivery_timesheet2.name,
                "product_id": self.product_delivery_timesheet2.id,
                "product_uom_qty": 50,
                "product_uom": self.product_delivery_timesheet2.uom_id.id,
                "price_unit": self.product_delivery_timesheet2.list_price,
                "order_id": self.sale_order_2.id,
            }
        )
        so_line_deliver_no_task = self.env["sale.order.line"].create(
            {
                "name": self.product_delivery_manual1.name,
                "product_id": self.product_delivery_manual1.id,
                "product_uom_qty": 50,
                "product_uom": self.product_delivery_manual1.uom_id.id,
                "price_unit": self.product_delivery_manual1.list_price,
                "order_id": self.sale_order_2.id,
            }
        )
        so_line_deliver_no_task.write({"qty_delivered": 1.0})

        self.sale_order_2.action_confirm()
        project_so = self.so_line_order_project.project_id
        # log timesheet for billable time
        timesheet1 = self._log_timesheet_manager(
            project_so, 10, so_line_deliver_global_project.task_id
        )
        task_so = self.so_line_order_project.task_id
        # logged some timesheets: on project only, then on tasks with different employees
        timesheet2 = self._log_timesheet_user(project_so, 2)
        timesheet3 = self._log_timesheet_user(project_so, 3, task_so)
        timesheet4 = self._log_timesheet_manager(project_so, 1, task_so)
        consumable1 = self._long_consumable_user(project_so, 3)
        # create a task which is not linked to sales order and fill non-billable timesheet
        task = self.env["project.task"].create(
            {
                "name": "Task",
                "project_id": project_so.id,
                "allow_billable": False,
                "sale_line_id": False,
            }
        )
        timesheet5 = self._log_timesheet_user(project_so, 5, task)
        consumable2 = self._long_consumable_user(project_so, 5, task=task)

        # invoice the Sales Order SO2
        context = {
            "active_model": "sale.order",
            "active_ids": [self.sale_order_2.id],
            "active_id": self.sale_order_2.id,
            "open_invoices": True,
        }

        payment = self.env["sale.advance.payment.inv"].create(
            {
                "advance_payment_method": "delivered",
            }
        )

        action_invoice = payment.with_context(context).create_invoices()
        invoice = self.env["account.move"].browse(action_invoice["res_id"])
        invoice.action_post()

        # simulate the auto creation of the SO line for expense, like we confirm a vendor bill.
        so_line_expense = self.env["sale.order.line"].create(
            {
                "name": self.product_expense.name,
                "product_id": self.product_expense.id,
                "product_uom_qty": 0.0,
                "product_uom": self.product_expense.uom_id.id,
                "price_unit": self.product_expense.list_price,  # reinvoice at sales price
                "order_id": self.sale_order_2.id,
                "is_expense": True,
            }
        )

        expense = self.env["account.analytic.line"].create(
            {
                "name": "expense on project_so",
                "account_id": project_so.analytic_account_id.id,
                "so_line": so_line_expense.id,
                "employee_id": self.employee_user.id,
                "unit_amount": 4,
                "amount": 4 * self.product_expense.list_price * -1,
                "product_id": self.product_expense.id,
                "product_uom_id": self.product_expense.uom_id.id,
            }
        )

        other_revenues = self.env["account.analytic.line"].create(
            {
                "name": "other revenues on project_so",
                "account_id": project_so.analytic_account_id.id,
                "employee_id": self.employee_user.id,
                "unit_amount": 1,
                "amount": self.product_expense.list_price,
                "product_id": self.product_expense.id,
                "product_uom_id": self.product_expense.uom_id.id,
            }
        )

        view_id = self.env.ref(
            "sale_timesheet.project_timesheet_action_client_timesheet_plan"
        ).id
        vals = self.env["project.project"]._qweb_prepare_qcontext(
            view_id, [["id", "=", project_so.id]]
        )

        dashboard_value = (
            timesheet2.unit_amount
            + timesheet3.unit_amount
            + timesheet4.unit_amount
            + timesheet5.unit_amount
            + timesheet1.unit_amount
        )
        project_so_timesheet_sold_unit = timesheet3.unit_amount + timesheet4.unit_amount
        project_rate_non_billable = round(
            timesheet5.unit_amount / dashboard_value * 100, 2
        )
        project_rate_non_billable_project = round(
            timesheet2.unit_amount / dashboard_value * 100, 2
        )
        project_rate_billable_time = round(
            timesheet1.unit_amount / dashboard_value * 100, 2
        )
        project_rate_billable_fixed = round(
            project_so_timesheet_sold_unit / dashboard_value * 100, 2
        )
        project_rate_total = (
            project_rate_non_billable
            + project_rate_non_billable_project
            + project_rate_billable_time
            + project_rate_billable_fixed
        )
        project_invoiced = (
            self.so_line_order_project.price_unit
            * self.so_line_order_project.product_uom_qty
            * timesheet1.unit_amount
        )
        project_timesheet_cost = (
            timesheet2.amount
            + timesheet3.amount
            + timesheet4.amount
            + timesheet5.amount
            + timesheet1.amount
        )
        project_other_revenues = invoice.invoice_line_ids.search(
            [("product_id", "=", self.product_delivery_manual1.id)]
        )
        project_consumable_cost = consumable1.amount + consumable2.amount

        self.assertEqual(
            float_compare(
                vals["dashboard"]["time"]["non_billable"],
                timesheet5.unit_amount,
                precision_rounding=rounding,
            ),
            0,
            "The hours non-billable should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["time"]["non_billable_project"],
                timesheet2.unit_amount,
                precision_rounding=rounding,
            ),
            0,
            "The hours non-billable-project should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["time"]["billable_time"],
                timesheet1.unit_amount,
                precision_rounding=rounding,
            ),
            0,
            "The hours billable-time should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["time"]["billable_fixed"],
                project_so_timesheet_sold_unit,
                precision_rounding=rounding,
            ),
            0,
            "The hours billable-fixed should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["time"]["total"],
                dashboard_value,
                precision_rounding=rounding,
            ),
            0,
            "The total hours should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["rates"]["non_billable"],
                project_rate_non_billable,
                precision_rounding=rounding,
            ),
            0,
            "The rate non-billable should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["rates"]["non_billable_project"],
                project_rate_non_billable_project,
                precision_rounding=rounding,
            ),
            0,
            "The rate non-billable-project should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["rates"]["billable_time"],
                project_rate_billable_time,
                precision_rounding=rounding,
            ),
            0,
            "The rate billable-time should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["rates"]["billable_fixed"],
                project_rate_billable_fixed,
                precision_rounding=rounding,
            ),
            0,
            "The rate billable-fixed should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["rates"]["total"],
                project_rate_total,
                precision_rounding=rounding,
            ),
            0,
            "The total rates should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["invoiced"],
                project_invoiced + project_other_revenues.price_total,
                precision_rounding=rounding,
            ),
            0,
            "The amount invoiced should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["cost"],
                project_timesheet_cost,
                precision_rounding=rounding,
            ),
            0,
            "The amount cost should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["expense_cost"],
                expense.amount,
                precision_rounding=rounding,
            ),
            0,
            "The amount expense-cost should be the one from the SO2 line, "
            "as we are in ordered quantity",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["other_revenues"],
                other_revenues.amount,
                precision_rounding=rounding,
            ),
            0,
            "The amount of the other revenues should be equal to the corresponding "
            "account move line and the one from the SO line",
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["expense_amount_untaxed_to_invoice"],
                -expense.amount,
                precision_rounding=rounding,
            ),
            0,
            "The amount of expense to re-invoice shoul be equal "
            "to the opposite of expense amount",
        )
        self.assertTrue(
            float_is_zero(
                vals["dashboard"]["profit"]["expense_amount_untaxed_invoiced"],
                precision_rounding=rounding,
            ),
            "The amount of expense re-invoiced should be equal to 0",
        )
        self.assertEqual(
            float_compare(
                vals["repartition_employee_max"], 11.0, precision_rounding=rounding
            ),
            0,
            "The amount of repartition-employee-max should be the one from SO2 line",
        )

        # PV consumable related tests
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["consumable_cost"],
                project_consumable_cost,
                precision_rounding=rounding,
            ),
            0,
        )
        self.assertEqual(
            float_compare(
                vals["dashboard"]["profit"]["total"],
                project_invoiced
                + project_timesheet_cost
                + other_revenues.amount
                + project_other_revenues.price_total
                + project_consumable_cost,
                precision_rounding=rounding,
            ),
            0,
            "The total amount should be the sum of the SO2 line "
            "and the created other_revenues account analytic line",
        )
        self.assertEqual(
            float_compare(
                vals["timesheet_forecast_table"]["rows"][-1][4],
                timesheet5.unit_amount,
                precision_rounding=rounding,
            ),
            0,
        )
        self.assertTrue(
            '["product_id", "!=", false]'
            in vals["stat_buttons"][-2]["action"]["data-domain"]
        )
        self.assertTrue(
            '["product_id", "=", false]'
            in vals["stat_buttons"][-1]["action"]["data-domain"],
            f'unexpected received domain {vals["stat_buttons"][-1]["action"]["data-domain"]}',
        )
