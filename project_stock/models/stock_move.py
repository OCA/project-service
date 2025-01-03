# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Related Task",
        check_company=True,
    )
    raw_material_task_id = fields.Many2one(
        comodel_name="project.task", string="Task for material", check_company=True
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """It is necessary to overwrite the name to prevent set product name
        from being auto-defined."""
        res = super()._onchange_product_id()
        if self.raw_material_task_id:
            self.name = self.raw_material_task_id.name
        return res

    def _prepare_analytic_line_from_task(self):
        product = self.product_id
        company_id = self.env.company
        task = self.task_id or self.raw_material_task_id
        analytic_account = (
            task.stock_analytic_account_id or task.project_id.analytic_account_id
        )
        if not analytic_account:
            return False
        res = {
            "date": (
                task.stock_analytic_date
                or task.project_id.stock_analytic_date
                or fields.date.today()
            ),
            "name": task.name + ": " + product.name,
            "unit_amount": self.quantity,
            "account_id": analytic_account.id,
            "user_id": self._uid,
            "product_uom_id": self.product_uom.id,
            "company_id": analytic_account.company_id.id or self.env.company.id,
            "partner_id": task.partner_id.id or task.project_id.partner_id.id or False,
            "stock_task_id": task.id,
        }
        amount_unit = product.with_context(uom=self.product_uom.id)._price_compute(
            "standard_price"
        )[product.id]
        amount = amount_unit * self.quantity or 0.0
        result = round(amount, company_id.currency_id.decimal_places) * -1
        vals = {"amount": result}
        analytic_line_fields = self.env["account.analytic.line"]._fields
        # Extra fields added in account addon
        if "ref" in analytic_line_fields:
            vals["ref"] = task.name
        if "product_id" in analytic_line_fields:
            vals["product_id"] = product.id
        # Prevent incoherence when hr_timesheet addon is installed.
        if "project_id" in analytic_line_fields:
            vals["project_id"] = False
        # distributions
        if task.stock_analytic_distribution:
            new_amount = 0
            for distribution in task.stock_analytic_distribution.values():
                new_amount -= (amount / 100) * distribution
            vals["amount"] = new_amount
        res.update(vals)
        return res

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self.env.context.get("default_raw_material_task_id"):
            task = self.env["project.task"].browse(
                self.env.context.get("default_raw_material_task_id")
            )
            if not task.group_id:
                task.group_id = self.env["procurement.group"].create(
                    task._prepare_procurement_group_vals()
                )
            defaults.update(
                {
                    "group_id": task.group_id.id,
                    "location_id": (
                        task.location_id.id or task.project_id.location_id.id
                    ),
                    "location_dest_id": (
                        task.location_dest_id.id or task.project_id.location_dest_id.id
                    ),
                    "picking_type_id": (
                        task.picking_type_id.id or task.project_id.picking_type_id.id
                    ),
                }
            )
        return defaults

    def action_task_product_forecast_report(self):
        self.ensure_one()
        action = self.product_id.action_product_forecast_report()
        action["context"] = {
            "active_id": self.product_id.id,
            "active_model": "product.product",
            "move_to_match_ids": self.ids,
        }
        warehouse = self.warehouse_id
        if warehouse:
            action["context"]["warehouse"] = warehouse.id
        return action


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Task",
        compute="_compute_task_id",
        store=True,
    )

    @api.depends("move_id.raw_material_task_id", "move_id.task_id")
    def _compute_task_id(self):
        for item in self:
            task = (
                item.move_id.raw_material_task_id
                if item.move_id.raw_material_task_id
                else item.move_id.task_id
            )
            item.task_id = task if task else False
