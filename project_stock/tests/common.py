# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common
from odoo.tests.common import new_test_user

from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT


class TestProjectStockBase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **DISABLED_MAIL_CONTEXT))
        cls.product_a = cls.env["product.product"].create(
            {"name": "Test product A", "detailed_type": "product", "standard_price": 10}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Test product B", "detailed_type": "product", "standard_price": 20}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "Test product C", "detailed_type": "product", "standard_price": 0}
        )
        cls.picking_type = cls.env.ref("project_stock.stock_picking_type_tm_test")
        cls.location = cls.picking_type.default_location_src_id
        cls.location_dest = cls.picking_type.default_location_dest_id
        cls.plan = cls.env["account.analytic.plan"].create(
            {
                "name": "Projects Plan",
            }
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Test account",
                "plan_id": cls.plan.id,
            },
        )
        cls.analytic_account_2 = cls.analytic_account.copy(
            {
                "name": "Test account 2",
                "plan_id": cls.plan.id,
            }
        )
        cls.project = cls.env.ref("project_stock.project_project_tm_test")
        cls.project.analytic_account_id = cls.analytic_account
        cls.stage_in_progress = cls.env.ref("project.project_stage_1")
        cls.stage_done = cls.env.ref("project.project_stage_2")
        group_stock_user = "stock.group_stock_user"
        cls.basic_user = new_test_user(
            cls.env,
            login="basic-user",
            groups="project.group_project_user,%s" % group_stock_user,
        )
        new_test_user(
            cls.env,
            login="manager-user",
            groups="project.group_project_manager,%s,analytic.group_analytic_accounting"
            % group_stock_user,
        )
        new_test_user(
            cls.env,
            login="project-task-user",
            groups="project.group_project_user,stock.group_stock_user",
        )

    def _prepare_context_task(self):
        return {
            "default_project_id": self.project.id,
            "default_stage_id": self.stage_in_progress.id,
            # We need to set default values according to compute store fields
            "default_location_id": self.project.location_id.id,
            "default_location_dest_id": self.project.location_dest_id.id,
            "default_picking_type_id": self.project.picking_type_id.id,
        }

    def _create_task(self, products):
        task_form = Form(
            self.env["project.task"].with_context(**self._prepare_context_task(self))
        )
        task_form.name = "Test task"
        # Save task to use default_get() correctlly in stock.moves
        task_form.save()
        for product in products:
            with task_form.move_ids.new() as move_form:
                move_form.product_id = product[0]
                move_form.product_uom_qty = product[1]
        return task_form.save()
