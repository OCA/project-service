# Copyright 2024 Tecnativa - Carlos López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    provision_product_id = fields.Many2one(
        "product.product",
        domain=[("type", "=", "service")],
    )
