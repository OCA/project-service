##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

import odoo.tests.common as common


class TestSaleOrderProject(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderProject, self).setUp()
        self.sale_order_model = self.env['sale.order']
        self.sale_order = self.env.ref('sale.sale_order_2')
        self.project = self.env.ref('project.project_project_1')

    def test_create_project_from_order(self):
        self.sale_order.action_create_project()
        project_dict = self.sale_order_model._prepare_project_vals(
            self.sale_order)
        project_name = self.sale_order.project_id.name
        self.assertEqual(self.sale_order.partner_id.id,
                         project_dict['partner_id'])
        self.assertEqual(project_name, project_dict['name'])
        self.assertEqual(self.sale_order.user_id.id, project_dict['user_id'])

