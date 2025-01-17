# Copyright 2024-today Numigi and all its contributors (https://bit.ly/numigiens)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Project Milestone Spent Hours",
    "version": "14.0.1.0.0",
    "author": "Numigi, Odoo Community Association (OCA)",
    "maintainer": "Numigi",
    "website": "https://github.com/OCA/project",
    "license": "AGPL-3",
    "category": "Project",
    "summary": """Add field Total Hours in milestones which display the sum
                of all hours of tasks associated to the milestone""",
    "depends": ["hr_timesheet", "project_milestone"],
    "data": [
        "views/project_milestone.xml",
        "views/project.xml",
    ],
    "installable": True,
}
