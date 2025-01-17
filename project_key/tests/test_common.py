# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo.tests.common import HttpCase, TransactionCase


class TestMixin:
    @staticmethod
    def _setup_records(class_or_instance):
        self = class_or_instance
        self.Project = self.env["project.project"].with_context(test_project_key=True)
        self.Task = self.env["project.task"].with_context(test_project_key=True)

        self.project_action = self.env.ref("project.open_view_project_all_config")
        self.task_action = self.env.ref("project.action_view_task")

        self.project_1 = self.Project.create({"name": "OCA"})
        self.project_2 = self.Project.create({"name": "Odoo", "key": "ODOO"})
        self.project_3 = self.Project.create({"name": "Python"})

        self.task11 = self.Task.create({"name": "1", "project_id": self.project_1.id})

        self.task12 = self.Task.create(
            {"name": "2", "parent_id": self.task11.id, "project_id": self.project_1.id}
        )

        self.task21 = self.Task.create({"name": "3", "project_id": self.project_2.id})

        self.task30 = self.Task.create({"name": "3"})

    def get_record_url(self, record, model, action):
        return f"/web#id={record.id}&view_type=form&model={model}&action={action}"

    def get_task_url(self, task):
        return self.get_record_url(task, task._name, self.task_action.id)

    def get_project_url(self, project):
        return self.get_record_url(project, project._name, self.project_action.id)


class TestCommon(TransactionCase, TestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls._setup_records(cls)


class HttpTestCommon(HttpCase, TestMixin):
    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, tracking_disable=True))
        self._setup_records(self)
