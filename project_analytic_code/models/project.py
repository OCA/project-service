# Copyright 2021 Pierre Verkest
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class Project(models.Model):
    _inherit = "project.project"

    analytic_account_code = fields.Char(
        string="Analytic code",
        related="analytic_account_id.code",
        store=True,
        index=True,
    )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        args = list(args or [])
        if name:
            args += ["|", ("analytic_account_code", "=", name)]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    def name_get(self):
        result = super().name_get()
        # Prepend analytic_account_code to display_name
        for i, (res_item, project) in enumerate(zip(result, self)):
            code = project.analytic_account_code
            if code:
                result[i] = (res_item[0], "[%s] %s" % (code, res_item[1]))
        return result
