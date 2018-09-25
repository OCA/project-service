# Copyright 2018 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError

from odoo.addons.project_task_scheduling.tests.common import \
    TestSchedulingCommon


class TestSchedulingProposal(TestSchedulingCommon):

    def test_action_recompute(self):
        self.wizard.action_accept()
        proposal_obj = self.env['project.task.scheduling.proposal']
        best_proposal = proposal_obj.search([])[-1]
        evaluation = best_proposal.evaluation
        new_proposal = best_proposal.copy()
        new_proposal.action_recompute()
        new_evaluation = new_proposal.evaluation
        self.assertEqual(evaluation, new_evaluation)

    def test_computed_fields(self):
        self.wizard.action_accept()
        proposals = self.env['project.task.scheduling.proposal'].search([])
        best_proposal = proposals[-1]
        date_end = best_proposal.date_end
        duration = best_proposal.duration
        delayed_tasks = best_proposal.delayed_tasks

        best_proposal._compute_end()
        best_proposal._compute_delayed_tasks()
        self.assertEqual(date_end, best_proposal.date_end)
        self.assertEqual(duration, best_proposal.duration)
        self.assertEqual(delayed_tasks, best_proposal.delayed_tasks)

    def test_action_approve(self):
        self.wizard.action_accept()
        proposals = self.env['project.task.scheduling.proposal'].search([])
        proposals[-1].action_timeline_scheduling()
        proposals[-1].action_approve()

        self.assertTrue(proposals[-1].state == 'approved')

        self.assertTrue(self.task_2.employee_id)
        self.assertTrue(self.task_2.date_start)
        self.assertTrue(self.task_2.date_end)

        self.assertTrue(self.task_3.employee_id)
        self.assertTrue(self.task_3.date_start)
        self.assertTrue(self.task_3.date_end)

        self.assertTrue(self.task_7.employee_id)
        self.assertTrue(self.task_7.date_start)
        self.assertTrue(self.task_7.date_end)

        self.assertTrue(self.task_1.employee_id)
        self.assertTrue(self.task_1.date_start)
        self.assertTrue(self.task_1.date_end)

    def test_action_reject(self):
        self.wizard.action_accept()
        proposals = self.env['project.task.scheduling.proposal'].search([])
        proposals[-1].action_reject()
        self.assertTrue(proposals[-1].state == 'rejected')

    def test_copy(self):
        self.wizard.action_accept()
        proposals = self.env['project.task.scheduling.proposal'].search([])
        proposals[-1].copy()
        proposals[-1].action_approve()
        with self.assertRaises(ValidationError):
            proposals[-1].copy()
