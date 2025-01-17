# Copyright 2023 - Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Project Task Description Template",
    "summary": "Add a description template to project tasks",
    "version": "18.0.1.0.0",
    "category": "Project Management",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/project",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["project"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule_data.xml",
        "views/project_task_view.xml",
        "views/project_task_description_template_view.xml",
    ],
}
