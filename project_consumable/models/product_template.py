# Copyright 2021 - Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    project_ok = fields.Boolean(
        string="Available in projects",
        help="Check this box to be able to link this product with "
        "analytic line and project or task. Product cost will be used "
        "and displayed in project dashboard as consumable cost. "
        "So you'll be able to analyse consumable products cost per project.",
    )

    @api.onchange("type")
    def _onchange_type(self):
        super()._onchange_type()
        if self.type == "consu":
            self.project_ok = True
        else:
            self.project_ok = False
