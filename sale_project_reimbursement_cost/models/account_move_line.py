from odoo import models
from odoo.tools import float_compare


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _sale_create_reinvoice_sale_line(self):
        """
        Generate an additional line in the sale order for the provision product
        only if the remaining amount in the provision product is greater than 0.
        - Sale lines with the same analytic account and reimbursement product.
        - Analytic lines with the same analytic account and provision product.
        """
        SaleLine = self.env["sale.order.line"]
        AnalyticLine = self.env["account.analytic.line"]
        map_sale_line_per_move = super()._sale_create_reinvoice_sale_line()
        for line in self.filtered(lambda aml: aml.product_id.provision_product_id):
            provision_product = line.product_id.provision_product_id
            sale_lines = map_sale_line_per_move.get(line.id) or []
            for sale_line in sale_lines:
                analytic_account_id = sale_line.order_id.analytic_account_id
                provision_data = AnalyticLine.read_group(
                    [
                        ("account_id", "=", analytic_account_id.id),
                        ("product_id", "=", provision_product.id),
                    ],
                    fields=["product_id", "amount:sum"],
                    groupby=["product_id"],
                )
                if not provision_data:
                    continue
                sale_reimbursement_data = SaleLine.read_group(
                    [
                        ("order_id.analytic_account_id", "=", analytic_account_id.id),
                        ("product_id", "=", line.product_id.id),
                        ("id", "!=", sale_line.id),
                        ("is_expense", "=", True),
                    ],
                    fields=["product_id", "untaxed_amount_to_invoice:sum"],
                    groupby=["product_id"],
                )
                reimbursement_amount = (
                    sale_reimbursement_data[0]["untaxed_amount_to_invoice"]
                    if sale_reimbursement_data
                    else 0.0
                )
                amount_remainig = max(
                    provision_data[0]["amount"] - reimbursement_amount, 0
                )
                amount = min(amount_remainig, line.price_subtotal)
                if (
                    float_compare(
                        amount, 0.0, precision_rounding=line.currency_id.rounding
                    )
                    <= 0
                ):
                    continue
                default_values = {
                    "product_id": provision_product.id,
                    "name": f"{line.name} ({provision_product.display_name})",
                    "price_unit": amount,
                    "product_uom_qty": -1,
                    "order_id": sale_line.order_id.id,
                    "is_expense": False,
                }
                sale_line.copy(default_values)
        return map_sale_line_per_move
