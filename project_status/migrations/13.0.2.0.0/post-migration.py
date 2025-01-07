# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Set current Project Status as not company limit"""
    env["project.status"].search([]).write({"company_id": False})
