# Copyright 2024 Tecnativa - Carlos López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.tools import format_date


class ProjectProject(models.Model):
    _inherit = "project.project"

    def get_panel_data(self):
        panel_data = super().get_panel_data()
        provision_items = self._get_provision_items()
        return {
            **panel_data,
            "provision_items": {"data": provision_items},
        }

    def _get_provision_items(self):
        if not self.user_has_groups("project.group_project_user"):
            return []
        provision_items = self.get_provision_items_data()
        reimbursement_items = self.get_reimbursement_items_data()
        data = provision_items + reimbursement_items
        data.sort(key=lambda x: f"{x.get('date')}_{x.get('id')}")
        return data

    def get_reimbursement_items_data(self):
        domain = self._get_reimbursement_items_domain()
        sols = self.env["sale.order.line"].sudo().search(domain)

        def get_action(res_id):
            """Return the action vals to call it in frontend to the sale lines"""
            action_id = "sale_project_reimbursement_cost.sol_reimbursement_cost_action"
            return {"action": {"name": action_id, "resId": res_id}}

        items = []
        for line in sols.with_context(with_price_unit=True):
            item = dict(
                {
                    "id": line.id,
                    "name": line.display_name,
                    "date": format_date(self.env, line.order_id.date_order),
                    "amount": -line.untaxed_amount_to_invoice,
                },
                **get_action(line.id),
            )
            items.append(item)
        return items

    def _get_reimbursement_items_domain(self):
        sale_items = self.sudo()._get_sale_order_items()
        domain = [
            ("order_id", "in", sale_items.sudo().order_id.ids),
            ("is_expense", "=", True),
            ("qty_to_invoice", ">", 0),
            ("state", "=", "sale"),
            ("display_type", "=", False),
            "|",
            ("project_id", "in", self.ids + [False]),
            ("id", "in", sale_items.ids),
        ]
        return domain

    def get_provision_items_data(self):
        domain = self._get_provision_items_domain()
        analytic_lines = (
            self.env["account.analytic.line"]
            .sudo()
            .search(
                domain,
                order="date,id",
            )
        )

        def get_action(res_id):
            """Return the action vals to call it in frontend to the analytic lines"""
            return {
                "action": {
                    "name": "analytic.account_analytic_line_action_entries",
                    "resId": res_id,
                }
            }

        items = []
        for analytic_line in analytic_lines:
            item = dict(
                {
                    "id": analytic_line.id,
                    "name": analytic_line.display_name,
                    "date": format_date(self.env, analytic_line.date),
                    "amount": analytic_line.amount,
                },
                **get_action(analytic_line.id),
            )
            items.append(item)
        return items

    def _get_provision_items_domain(self):
        provision_products = self.sudo()._get_provision_products()
        domain = [
            ("product_id", "in", provision_products.ids),
            ("account_id", "=", self.analytic_account_id.id),
        ]
        return domain

    def _get_provision_products(self):
        """Get the provision products set in the all products"""
        provision_products = self.env["product.template"]._read_group(
            domain=[("provision_product_id", "!=", False)],
            groupby=[],
            aggregates=["provision_product_id:recordset"],
        )
        return (
            provision_products[0][0]
            if provision_products
            else self.env["product.product"]
        )
