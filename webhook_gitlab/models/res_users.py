# Copyright 2020, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    gitlab_username = fields.Char()
    github_username = fields.Char()
