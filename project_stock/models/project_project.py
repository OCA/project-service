# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        readonly=False,
        domain="[('company_id', '=', company_id)]",
        index=True,
        check_company=True,
    )
    location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Source Location",
        readonly=False,
        check_company=True,
        index=True,
        help="Default location from which materials are consumed.",
    )
    location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination Location",
        readonly=False,
        index=True,
        check_company=True,
        help="Default location to which materials are consumed.",
    )
    stock_analytic_date = fields.Date(string="Analytic date")

    @api.onchange("picking_type_id")
    def _onchange_picking_type_id(self):
        self.location_id = self.picking_type_id.default_location_src_id.id
        self.location_dest_id = self.picking_type_id.default_location_dest_id.id

    def write(self, vals):
        """Update location information on pending moves when changed."""
        res = super().write(vals)
        field_names = ("location_id", "location_dest_id")
        if any(vals.get(field) for field in field_names):
            self.task_ids._update_moves_info()
        return res
