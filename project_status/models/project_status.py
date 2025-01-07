from odoo import api, fields, models


class ProjectStatus(models.Model):
    _name = "project.status"
    _order = "status_sequence"
    _description = "Project Status"

    name = fields.Char(
        required=True,
        translate=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    description = fields.Char(translate=True)
    status_sequence = fields.Integer(string="Sequence")
    is_closed = fields.Boolean(
        string="Is Closed Status",
        help="Specify if this is a closing status.",
    )
    fold = fields.Boolean(string="Folded")

    @api.model
    def create(self, vals):
        seq = self.env["ir.sequence"].next_by_code("project.status") or 0
        vals["status_sequence"] = seq
        return super(ProjectStatus, self).create(vals)
