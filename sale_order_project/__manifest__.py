# Copyright 2013 Benoît GUILLOT <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sale Order Project',
    'version': '12.0.1.0.0',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'author': 'Akretion, '
              'AvanzOSC, '
              'Serv. Tecnol. Avanzados - Pedro M. Baeza, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/project',
    'depends': [
        'analytic',
        'project',
        'sale',
    ],
    'data': [
        'views/sale_view.xml',
    ],
    'installable': True,
}
