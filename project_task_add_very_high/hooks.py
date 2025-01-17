# Copyright 2017-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def uninstall_hook(env):
    # Convert priority from High and Very High to Normal
    # to avoid inconsistency after the module is uninstalled
    env["project.task"].sudo().search([("priority", "in", ["2", "3"])]).write(
        {"priority": "1"}
    )
