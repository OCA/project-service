# Copyright 2016-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Project Task Add Very High",
    "summary": "Adds extra options 'High' and 'Very High' on tasks",
    "version": "18.0.1.0.0",
    "development_status": "Production/Stable",
    "author": "Onestein, Odoo Community Association (OCA)",
    "maintainers": ["astirpe"],
    "license": "AGPL-3",
    "category": "Project",
    "website": "https://github.com/OCA/project",
    "depends": ["project"],
    "data": ["views/project_task_view.xml"],
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
