{
    "name": "Project Status",
    "summary": """
        Project Status""",
    "author": "Patrick Wilson, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/project",
    "category": "Project Management",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["project"],
    "data": [
        "views/project_status.xml",
        "views/project.xml",
        "security/ir.model.access.csv",
        "security/project_status.xml",
        "data/data.xml",
    ],
    "application": False,
    "development_status": "Beta",
    "maintainers": ["patrickrwilson"],
}
