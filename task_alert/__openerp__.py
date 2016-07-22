# -*- coding: utf-8 -*-
# © 2016 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Task Reminder Planner",
    'summary': """Plan task reminders for any date field.""",
    'author': "ONESTEiN BV,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': "http://www.onestein.eu",
    'images': ['static/description/main_screenshot.png'],
    'category': 'Custom',
    'version': '8.0.1.0.0',
    'depends': [
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/task_alert.xml',
        'data/task_alert_cron.xml',
    ],
    'installable': True,
}
