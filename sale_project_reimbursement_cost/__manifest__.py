# Copyright 2024 Tecnativa - Carlos López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale project reimbursement cost",
    "version": "17.0.1.0.0",
    "summary": """Display provisions and reimbursement costs
        in the Project Updates dashboard.""",
    "author": "Tecnativa,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/project",
    "category": "Sales",
    "depends": [
        "sale_project",
    ],
    "data": ["views/product_template_views.xml", "views/sale_order_line_views.xml"],
    "demo": ["demo/product_demo.xml"],
    "assets": {
        "web.assets_backend": [
            "sale_project_reimbursement_cost/static/src/components/project_right_side_panel/**/*",
        ],
    },
    "installable": True,
    "license": "AGPL-3",
}
