# Copyright 2025 Ángel García de la Chica <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Project Task Required Project",
    "summary": "Obligation to specify a project when creating/editing a task",
    "version": "15.0.1.0.0",
    "category": "Project",
    "website": "https://github.com/OCA/project",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["project"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
}
