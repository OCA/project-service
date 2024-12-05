# Copyright 2024 Tecnativa - Carlos López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import new_test_user, tagged
from odoo.tests.common import users

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


@tagged("post_install", "-at_install")
class TestReimbursementCost(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.Task = cls.env["project.task"]
        cls.Product = cls.env["product.product"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.SaleLine = cls.env["sale.order.line"]
        cls.user = new_test_user(
            cls.env,
            login="test-user",
            groups="sales_team.group_sale_salesman"
            ",project.group_project_user"
            ",analytic.group_analytic_accounting",
        )
        cls.service_task = cls.env.ref(
            "sale_project_reimbursement_cost.product_service_task"
        )
        cls.service_provision = cls.env.ref(
            "sale_project_reimbursement_cost.product_provision"
        )
        cls.service_reimbursement = cls.env.ref(
            "sale_project_reimbursement_cost.product_reimbursement"
        )
        cls.sale_order = cls.SaleOrder.create(
            {
                "partner_id": cls.partner_a.id,
                "partner_invoice_id": cls.partner_a.id,
                "partner_shipping_id": cls.partner_a.id,
            }
        )
        cls.sol_task = cls.SaleLine.create(
            {
                "product_id": cls.service_task.id,
                "product_uom_qty": 1,
                "order_id": cls.sale_order.id,
            }
        )
        cls.sol_provision = cls.SaleLine.create(
            {
                "product_id": cls.service_provision.id,
                "product_uom_qty": 1,
                "order_id": cls.sale_order.id,
                "price_unit": 1000,
            }
        )
        cls.bill_1 = cls.init_invoice("in_invoice", products=cls.service_reimbursement)

    @users("test-user")
    def test_reimbursement_cost(self):
        """
        Create a sale order with a task and a provision product.
        Generate a bill with a reimbursement product by 400.
        Check that the provision line is added to the sale order.
        Invoice the sale order.
        Generate a new bill with a reimbursement product by 600.
        Check that the provision line is added to the sale order.
        Invoice the sale order.
        Generate a new bill with a reimbursement product by 100.
        Check that the provision line is not added to the sale order.
        Invoice the sale order.
        """

        def _get_provision_and_reimbursement(project):
            project_report_values = project.get_panel_data()
            provision_data = project_report_values["provision_items"]["data"]
            provisions = list(filter(lambda x: x["amount"] > 0, provision_data))
            reimbursements = list(filter(lambda x: x["amount"] < 0, provision_data))
            return provisions, reimbursements

        # generate the project/task and provision
        self.sale_order.action_confirm()
        customer_invoice = self.sale_order._create_invoices()
        customer_invoice.action_post()
        self.assertTrue(self.sol_task.task_id)
        self.assertTrue(self.sale_order.analytic_account_id)
        project = self.sol_task.task_id.project_id
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(reimbursement_items), 0)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        # generate the reimbursement
        self.bill_1.invoice_line_ids.write(
            {
                "analytic_distribution": {project.analytic_account_id.id: 100},
                "price_unit": 400,
                "quantity": 1,
            }
        )
        self.bill_1.action_post()
        # Check that the new lines are added to the sale order
        # 1 line for reimbursement and 1 line for provision
        self.assertEqual(len(self.sale_order.order_line), 4)
        reimbursement_line = self.sale_order.order_line.filtered("is_expense")
        reimbursement_provision_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.service_provision
            and not line.is_expense
            and line.product_uom_qty < 0
        )
        self.assertEqual(len(reimbursement_provision_line), 1)
        self.assertEqual(reimbursement_line.untaxed_amount_to_invoice, 400)
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        self.assertEqual(len(reimbursement_items), 1)
        self.assertEqual(reimbursement_items[0]["amount"], -400)
        self.assertIn("Reimbursement", reimbursement_items[0]["name"])
        # invoice the sale order.
        customer_invoice = self.sale_order._create_invoices(final=True)
        customer_invoice.action_post()
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        self.assertEqual(len(reimbursement_items), 1)
        self.assertEqual(reimbursement_items[0]["amount"], -400)
        self.assertIn("Provision", reimbursement_items[0]["name"])
        # generate a second reimbursement by 600
        new_bill = self.bill_1.copy()
        new_bill.invoice_date = "2024-01-01"
        new_bill.invoice_line_ids.write(
            {
                "analytic_distribution": {project.analytic_account_id.id: 100},
                "price_unit": 600,
                "quantity": 1,
            }
        )
        new_bill.action_post()
        # Check that the new lines are added to the sale order
        # 1 line for reimbursement and 1 line for provision
        self.assertEqual(len(self.sale_order.order_line), 6)
        reimbursement_line = self.sale_order.order_line.filtered("is_expense")
        reimbursement_provision_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.service_provision
            and not line.is_expense
            and line.product_uom_qty < 0
        )
        self.assertEqual(len(reimbursement_provision_line), 2)
        self.assertEqual(len(reimbursement_line), 2)
        self.assertEqual(reimbursement_line[0].untaxed_amount_to_invoice, 0)
        self.assertEqual(reimbursement_line[1].untaxed_amount_to_invoice, 600)
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        self.assertEqual(len(reimbursement_items), 2)
        self.assertEqual(reimbursement_items[0]["amount"], -400)
        self.assertEqual(reimbursement_items[1]["amount"], -600)
        self.assertIn("Reimbursement", reimbursement_items[0]["name"])
        self.assertIn("Reimbursement", reimbursement_items[1]["name"])
        # invoice the sale order.
        customer_invoice = self.sale_order._create_invoices(final=True)
        customer_invoice.action_post()
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        self.assertEqual(len(reimbursement_items), 2)
        self.assertEqual(reimbursement_items[0]["amount"], -400)
        self.assertEqual(reimbursement_items[1]["amount"], -600)
        self.assertIn("Provision", reimbursement_items[0]["name"])
        # generate a new reimbursement by 100
        # but the provision line must be not added
        # only the reimbursement line must be added
        new_bill = self.bill_1.copy()
        new_bill.invoice_date = "2024-01-01"
        new_bill.invoice_line_ids.write(
            {
                "analytic_distribution": {project.analytic_account_id.id: 100},
                "price_unit": 100,
                "quantity": 1,
            }
        )
        new_bill.action_post()
        # Check that the new lines are added to the sale order
        # 1 line for reimbursement and no line for provision
        self.assertEqual(len(self.sale_order.order_line), 7)
        reimbursement_line = self.sale_order.order_line.filtered("is_expense")
        reimbursement_provision_line = self.sale_order.order_line.filtered(
            lambda line: line.product_id == self.service_provision
            and not line.is_expense
            and line.product_uom_qty < 0
        )
        self.assertEqual(len(reimbursement_provision_line), 2)
        self.assertEqual(len(reimbursement_line), 3)
        self.assertEqual(reimbursement_line[0].untaxed_amount_to_invoice, 0)
        self.assertEqual(reimbursement_line[1].untaxed_amount_to_invoice, 0)
        self.assertEqual(reimbursement_line[2].untaxed_amount_to_invoice, 100)
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        self.assertEqual(len(reimbursement_items), 3)
        self.assertEqual(reimbursement_items[0]["amount"], -400)
        self.assertEqual(reimbursement_items[1]["amount"], -600)
        self.assertEqual(reimbursement_items[2]["amount"], -100)
        self.assertIn("Reimbursement", reimbursement_items[0]["name"])
        self.assertIn("Reimbursement", reimbursement_items[1]["name"])
        self.assertIn("Reimbursement", reimbursement_items[2]["name"])
        # invoice the sale order.
        customer_invoice = self.sale_order._create_invoices(final=True)
        customer_invoice.action_post()
        provision_items, reimbursement_items = _get_provision_and_reimbursement(project)
        self.assertEqual(len(provision_items), 1)
        self.assertEqual(provision_items[0]["amount"], 1000)
        self.assertEqual(len(reimbursement_items), 2)
        self.assertEqual(reimbursement_items[0]["amount"], -400)
        self.assertEqual(reimbursement_items[1]["amount"], -600)
        self.assertIn("Provision", reimbursement_items[0]["name"])
