from odoo import SUPERUSER_ID, api, fields, models


class Project(models.Model):
    _inherit = "project.project"

    @api.model
    def _read_group_status_ids(self, statuses, domain, order):
        statuse_ids = statuses._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return statuses.browse(statuse_ids)

    project_status = fields.Many2one(
        comodel_name="project.status",
        group_expand="_read_group_status_ids",
        copy=False,
        ondelete="restrict",
        index=True,
    )
