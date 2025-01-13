# Copyright 2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # 14.0.2.0.0 renames the field already
    if [int(c) for c in version.split(".")] >= [14, 0, 2, 0, 0]:
        return
    openupgrade.rename_fields(
        env, [("project.task", "project_task", "date_start", "planned_date_start")]
    )
