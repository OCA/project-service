from odoo import fields, models


class ProjectProjectStage(models.Model):
    _inherit = "project.project.stage"

    description = fields.Char(translate=True)
    is_closed = fields.Boolean(
        string="Is Closed Stage",
        help="Specify if this is a closing stage.",
    )
