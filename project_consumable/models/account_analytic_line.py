# Copyright 2021 - Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _timesheet_preprocess(self, vals):
        """Deduce other field values from the one given.
        Overrride this to compute on the fly some field that can not be computed fields.
        :param values: dict values for `create`or `write`.
        """
        if all(v in vals for v in ["product_id", "project_id"]):
            if "product_uom_id" not in vals:
                product = self.env["product.product"].sudo().browse(vals["product_id"])
                vals["product_uom_id"] = product.uom_id.id
        return super()._timesheet_preprocess(vals)

    def _timesheet_postprocess_values(self, values):
        """Get the addionnal values to write on record
        :param dict values: values for the model's fields, as a dictionary::
            {'field_name': field_value, ...}
        :return: a dictionary mapping each record id to its corresponding
            dictionary values to write (may be empty).
        """
        result = super()._timesheet_postprocess_values(values)
        sudo_self = self.sudo()
        if any(
            field_name in values
            for field_name in [
                "unit_amount",
                "product_id",
                "account_id",
                "product_uom_id",
            ]
        ):
            for material in sudo_self:
                if material.project_id and material.product_id:
                    cost = material.product_id.standard_price or 0.0
                    qty = material.unit_amount
                    if (
                        material.product_uom_id
                        and material.product_id.uom_id
                        and material.product_uom_id != material.product_id.uom_id
                    ):
                        qty = material.product_uom_id._compute_quantity(
                            qty,
                            material.product_id.uom_id,
                        )
                    amount = -1 * qty * cost
                    amount_converted = material.product_id.currency_id._convert(
                        amount,
                        material.account_id.currency_id,
                        self.env.company,
                        material.date,
                    )
                    result[material.id].update(
                        {
                            "amount": amount_converted,
                        }
                    )
        return result
