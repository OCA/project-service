# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import TestProjectStockBase


class TestProjectStock(TestProjectStockBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.task = cls._create_task(cls, [(cls.product_a, 2), (cls.product_b, 1)])
        cls.move_product_a = cls.task.move_ids.filtered(
            lambda x: x.product_id == cls.product_a
        )
        cls.move_product_b = cls.task.move_ids.filtered(
            lambda x: x.product_id == cls.product_b
        )

    def test_project_task_misc(self):
        self.assertFalse(self.task.picking_type_id)
        self.assertFalse(self.task.location_id)
        self.assertFalse(self.task.location_dest_id)
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
        self.assertEqual(len(self.task.stock_analytic_line_ids), 2)
        self.assertEqual(
            sum(self.task.stock_analytic_line_ids.mapped("unit_amount")), 3
        )
        self.assertEqual(
            sum(self.task.stock_analytic_line_ids.mapped("amount")), amount
        )
        self.assertEqual(
            self.task.stock_analytic_tag_ids,
            self.task.stock_analytic_line_ids.mapped("tag_ids"),
        )
        self.assertIn(
            self.analytic_account,
            self.task.stock_analytic_line_ids.mapped("account_id"),
        )

    def test_project_task_without_analytic_account(self):
        # Prevent error when hr_timesheet addon is installed.
        if "allow_timesheets" in self.task.project_id._fields:
            self.task.project_id.allow_timesheets = False
        self.task.project_id.analytic_account_id = False
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self.assertFalse(self.task.stock_analytic_line_ids)

    def test_project_task_analytic_lines_without_tags(self):
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self._test_task_analytic_lines_from_task(-40)

    def test_project_task_analytic_lines_with_tag_1(self):
        self.task.write({"stock_analytic_tag_ids": self.analytic_tag_1.ids})
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self._test_task_analytic_lines_from_task(-40)

    def test_project_task_analytic_lines_with_tag_2(self):
        self.task.write({"stock_analytic_tag_ids": self.analytic_tag_2.ids})
        self.task.write({"stage_id": self.stage_done.id})
        self.task.action_done()
        self._test_task_analytic_lines_from_task(-20)

    def test_project_task_process_done(self):
        self.assertEqual(self.move_product_a.state, "draft")
        self.assertEqual(self.move_product_b.state, "draft")
        # Change task stage (auto-confirm + auto-assign)
        self.task.write({"stage_id": self.stage_done.id})
        self.assertEqual(self.move_product_a.state, "assigned")
        self.assertEqual(self.move_product_b.state, "assigned")
        self.assertEqual(self.move_product_a.reserved_availability, 2)
        self.assertEqual(self.move_product_b.reserved_availability, 1)
        # action_done
        self.task.action_done()
        self.assertEqual(self.move_product_a.state, "done")
        self.assertEqual(self.move_product_b.state, "done")
        self.assertEqual(self.move_product_a.quantity_done, 2)
        self.assertEqual(self.move_product_b.quantity_done, 1)

    def test_project_task_process_cancel(self):
        self.assertEqual(self.move_product_a.state, "draft")
        self.assertEqual(self.move_product_b.state, "draft")
        # Change task stage
        self.task.write({"stage_id": self.stage_done.id})
        self.assertEqual(self.move_product_a.state, "assigned")
        self.assertEqual(self.move_product_b.state, "assigned")
        # action_cancel
        self.task.action_cancel()
        self.assertEqual(self.move_product_a.state, "cancel")
        self.assertEqual(self.move_product_b.state, "cancel")

    def test_project_task_process_unreserve(self):
        self.assertEqual(self.move_product_a.state, "draft")
        self.assertEqual(self.move_product_b.state, "draft")
        # Change task stage (auto-confirm + auto-assign)
        self.task.write({"stage_id": self.stage_done.id})
        self.assertTrue(self.move_product_a.move_line_ids)
        self.assertEqual(self.move_product_a.move_line_ids.task_id, self.task)
        self.assertEqual(self.move_product_a.state, "assigned")
        self.assertEqual(self.move_product_b.state, "assigned")
        self.assertEqual(self.move_product_a.reserved_availability, 2)
        self.assertEqual(self.move_product_b.reserved_availability, 1)
        self.assertTrue(self.task.unreserve_visible)
        # button_unreserve
        self.task.button_unreserve()
        self.assertEqual(self.move_product_a.state, "confirmed")
        self.assertEqual(self.move_product_b.state, "confirmed")
        self.assertEqual(self.move_product_a.reserved_availability, 0)
        self.assertEqual(self.move_product_b.reserved_availability, 0)
        self.assertFalse(self.task.unreserve_visible)
