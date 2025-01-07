# Copyright 2021 - Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from . import models


from odoo import api, fields, SUPERUSER_ID


def set_project_ok_for_consumable_products(cr, _):
    env = api.Environment(cr, SUPERUSER_ID, {})

    env["product.product"].search([("type", "=", "consu")]).write({"project_ok": True})
