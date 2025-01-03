# Copyright 2022-2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import Form
from odoo.tests.common import users
from odoo.tools import mute_logger

from .common import TestProjectStockBase


class TestProjectStock(TestProjectStockBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_stock_quant(cls, cls.product_a, cls.location, 2)
        cls._create_stock_quant(cls, cls.product_b, cls.location, 1)
        cls._create_stock_quant(cls, cls.product_c, cls.location, 1)
        cls.task = cls._create_task(cls, [(cls.product_a, 2), (cls.product_b, 1)])
        cls.move_product_a = cls.task.move_ids.filtered(
            lambda x: x.product_id == cls.product_a
        )
        cls.move_product_b = cls.task.move_ids.filtered(
            lambda x: x.product_id == cls.product_b
        )
        cls.env.ref("base.user_admin").write(
            {
                "groups_id": [
                    (4, cls.env.ref("analytic.group_analytic_accounting").id),
                ],
            }
        )

    def _create_stock_quant(self, product, location, qty):
        self.env["stock.quant"].create(
            {"product_id": product.id, "location_id": location.id, "quantity": qty}
        )

    def test_project_task_misc(self):
        self.assertTrue(self.task.group_id)
        self.assertEqual(self.task.picking_type_id, self.picking_type)
        self.assertEqual(self.task.location_id, self.location)
        self.assertEqual(self.task.location_dest_id, self.location_dest)
        self.assertEqual(self.move_product_a.name, self.task.name)
        self.assertEqual(self.move_product_a.reference, self.task.name)
        self.assertEqual(self.move_product_a.location_id, self.location)
        self.assertEqual(self.move_product_a.location_dest_id, self.location_dest)
        self.assertEqual(self.move_product_a.picking_type_id, self.picking_type)
        self.assertEqual(self.move_product_a.raw_material_task_id, self.task)
        self.assertEqual(self.move_product_b.location_id, self.location)
        self.assertEqual(self.move_product_b.location_dest_id, self.location_dest)
        self.assertEqual(self.move_product_b.picking_type_id, self.picking_type)
        self.assertEqual(self.move_product_b.raw_material_task_id, self.task)

    def _test_task_analytic_lines_from_task(self, amount):
        self.task = self.env["project.task"].browse(self.task.id)
        # Prevent error when hr_timesheet addon is installed.
        stock_analytic_lines = self.task.sudo().stock_analytic_line_ids
        self.assertEqual(len(stock_analytic_lines), 2)
        self.assertEqual(sum(stock_analytic_lines.mapped("unit_amount")), 3)
        self.assertEqual(sum(stock_analytic_lines.mapped("amount")), amount)
        self.assertIn(
            self.analytic_account,
            stock_analytic_lines.mapped("account_id"),
        )
        # Prevent incoherence when hr_timesheet addon is installed.
        if "project_id" in self.task.stock_analytic_line_ids._fields:
            self.assertFalse(self.task.stock_analytic_line_ids.project_id)

    def test_project_task_without_analytic_account(self):
        self.task = self.env["project.task"].browse(self.task.id)
        # Prevent error when hr_timesheet addon is installed.
        if "allow_timesheets" in self.task.project_id._fields:
            self.task.project_id.allow_timesheets = False
        self.task.project_id.analytic_account_id = False
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self.assertFalse(self.task.stock_analytic_line_ids)

    @users("manager-user")
    def test_project_task_without_analytic_account_manager_user(self):
        self.test_project_task_without_analytic_account()

    def test_project_task_user_access_without_stock_group(self):
        self.basic_user.write(
            {
                "groups_id": [(6, 0, [self.env.ref("project.group_project_user").id])],
            }
        )
        task_form = Form(self.task.with_user(self.basic_user))
        self.assertEqual(task_form.project_id, self.project)

    def test_project_task_analytic_lines_without_tags(self):
        self.task = self.env["project.task"].browse(self.task.id)
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self._test_task_analytic_lines_from_task(-40)
        self.assertEqual(
            fields.first(self.task.stock_analytic_line_ids).date,
            fields.Date.from_string("1990-01-01"),
        )

    @users("manager-user")
    def test_project_task_analytic_lines_without_tags_manager_user(self):
        self.test_project_task_analytic_lines_without_tags()

    def test_project_task_analytic_lines_with_tag_1(self):
        self.task = self.env["project.task"].browse(self.task.id)
        self.task.write(
            {
                "stock_analytic_date": "1991-01-01",
            }
        )
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self._test_task_analytic_lines_from_task(-40)
        self.assertEqual(
            fields.first(self.task.stock_analytic_line_ids).date,
            fields.Date.from_string("1991-01-01"),
        )

    @users("manager-user")
    def test_project_task_analytic_lines_with_tag_1_manager_user(self):
        self.task.stock_analytic_distribution = {self.analytic_account.id: 100}
        self.test_project_task_analytic_lines_with_tag_1()

    def test_project_task_analytic_lines_with_tag_2(self):
        self.task = self.env["project.task"].browse(self.task.id)
        self.task.project_id.stock_analytic_date = False
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self._test_task_analytic_lines_from_task(-40)
        self.assertEqual(
            fields.first(self.task.stock_analytic_line_ids).date, fields.date.today()
        )

    @users("manager-user")
    def test_project_task_analytic_lines_with_tag_2_manager_user(self):
        self.task.stock_analytic_distribution = {
            self.analytic_account.id: 50,
            self.analytic_account_2.id: 50,
        }
        self.test_project_task_analytic_lines_with_tag_2()

    def test_project_task_process_done(self):
        self.task = self.env["project.task"].browse(self.task.id)
        self.assertEqual(self.move_product_a.state, "draft")
        self.assertEqual(self.move_product_b.state, "draft")
        # Change task stage (auto-confirm + auto-assign)
        self.task.write({"stage_id": self.stage_done.id})
        self.assertEqual(self.move_product_a.state, "assigned")
        self.assertEqual(self.move_product_b.state, "assigned")
        self.assertEqual(self.move_product_a.quantity, 2)
        self.assertEqual(self.move_product_b.quantity, 1)
        self.assertTrue(self.task.stock_moves_is_locked)
        self.task.action_toggle_stock_moves_is_locked()
        self.assertFalse(self.task.stock_moves_is_locked)
        # Add new stock_move
        self.task.write({"stage_id": self.stage_in_progress.id})
        task_form = Form(self.task)
        with task_form.move_ids.new() as move_form:
            move_form.product_id = self.product_c
            move_form.product_uom_qty = 1
        task_form.save()
        move_product_c = self.task.move_ids.filtered(
            lambda x: x.product_id == self.product_c
        )
        self.assertEqual(move_product_c.state, "draft")
        self.task.action_assign()
        self.assertEqual(move_product_c.state, "assigned")
        self.task.write({"stage_id": self.stage_done.id})
        # action_done
        self.task.action_done()
        self.assertEqual(self.move_product_a.state, "done")
        self.assertEqual(self.move_product_b.state, "done")
        self.assertEqual(self.move_product_a.quantity, 2)
        self.assertEqual(self.move_product_b.quantity, 1)
        self.assertEqual(move_product_c.quantity, 1)

    @users("basic-user")
    def test_project_task_process_done_basic_user(self):
        self.test_project_task_process_done()

    @mute_logger("odoo.models.unlink")
    def test_project_task_process_cancel(self):
        self.task = self.env["project.task"].browse(self.task.id)
        self.assertEqual(self.move_product_a.state, "draft")
        self.assertEqual(self.move_product_b.state, "draft")
        # Change task stage
        self.task.write({"stage_id": self.stage_done.id})
        self.assertEqual(self.move_product_a.state, "assigned")
        self.assertEqual(self.move_product_b.state, "assigned")
        # action_done
        self.task.action_done()
        self.assertEqual(self.move_product_a.state, "done")
        self.assertEqual(self.move_product_b.state, "done")
        self.assertEqual(self.move_product_a.quantity, 2)
        self.assertEqual(self.move_product_b.quantity, 1)
        self.assertTrue(self.task.sudo().stock_analytic_line_ids)
        # action_cancel
        self.task.action_cancel()
        self.assertEqual(self.move_product_a.state, "done")
        self.assertEqual(self.move_product_b.state, "done")
        self.assertEqual(self.move_product_a.quantity, 0)
        self.assertEqual(self.move_product_b.quantity, 0)
        self.assertFalse(self.task.stock_analytic_line_ids)
        quant_a = self.product_a.stock_quant_ids.filtered(
            lambda x: x.location_id == self.location
        )
        quant_b = self.product_b.stock_quant_ids.filtered(
            lambda x: x.location_id == self.location
        )
        quant_c = self.product_c.stock_quant_ids.filtered(
            lambda x: x.location_id == self.location
        )
        self.assertEqual(quant_a.quantity, 2)
        self.assertEqual(quant_b.quantity, 1)
        self.assertEqual(quant_c.quantity, 1)

    @users("manager-user")
    def test_project_task_process_cancel_manager_user(self):
        self.test_project_task_process_cancel()

    @mute_logger("odoo.models.unlink")
    def test_project_task_process_01(self):
        """Product A move cancel + Product B move OK."""
        self.task = self.env["project.task"].browse(self.task.id)
        self.move_product_b.unlink()
        self.assertEqual(self.move_product_a.state, "draft")
        # Confirm + Edit to qty=0
        self.task.action_confirm()
        self.assertEqual(self.move_product_a.state, "assigned")
        self.move_product_a.product_uom_qty = 0
        self.task.action_done()
        self.assertEqual(self.move_product_a.state, "cancel")
        # Add extra line
        task_form = Form(self.task)
        with task_form.move_ids.new() as move_form:
            move_form.product_id = self.product_b
            move_form.product_uom_qty = 1
        task_form.save()
        self.move_product_b = self.task.move_ids.filtered(
            lambda x: x.product_id == self.product_b
        )
        self.task.action_confirm()
        self.assertEqual(self.move_product_b.state, "assigned")
        self.task.action_done()
        self.assertEqual(self.move_product_b.state, "done")

    def test_project_task_process_02(self):
        self.task.action_confirm()
        self.assertEqual(self.move_product_a.state, "assigned")
        self.assertEqual(self.move_product_b.state, "assigned")
        self.task.action_done()
        self.assertEqual(self.move_product_a.state, "done")
        self.assertEqual(self.move_product_b.state, "done")
        self.assertEqual(len(self.task.stock_analytic_line_ids), 2)
        self.task.action_done()

    def test_project_task_action_cancel(self):
        self.assertTrue(self.env["project.task"].browse(self.task.id).action_cancel())

    @users("basic-user")
    def test_project_task_action_cancel_basic_user(self):
        self.test_project_task_action_cancel()

    def test_project_task_action_done(self):
        self.task = self.env["project.task"].browse(self.task.id)
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self.assertTrue(self.task.sudo().stock_analytic_line_ids)

    @users("basic-user")
    def test_project_task_action_done_basic_user(self):
        self.test_project_task_action_done()

    @mute_logger("odoo.models.unlink")
    def test_project_task_unlink(self):
        self.assertTrue(self.env["project.task"].browse(self.task.id).unlink())

    @users("basic-user")
    def test_project_task_unlink_basic_user(self):
        self.test_project_task_unlink()

    @mute_logger("odoo.models.unlink")
    def test_project_project_onchange(self):
        new_type = self.env.ref("stock.picking_type_out")
        self.project.write({"picking_type_id": new_type.id})
        self.project._onchange_picking_type_id()
        self.assertEqual(self.project.location_id, new_type.default_location_src_id)
        self.assertEqual(
            self.project.location_dest_id, new_type.default_location_dest_id
        )
        move = fields.first(self.task.move_ids)
        self.assertEqual(move.location_id, new_type.default_location_src_id)

    def test_project_task_scrap(self):
        move = fields.first(self.task.move_ids)
        scrap = self.env["stock.scrap"].create(
            {
                "product_id": move.product_id.id,
                "product_uom_id": move.product_id.uom_id.id,
                "scrap_qty": 1,
                "task_id": self.task.id,
            }
        )
        scrap.do_scrap()
        self.assertEqual(scrap.move_ids.raw_material_task_id, self.task)
