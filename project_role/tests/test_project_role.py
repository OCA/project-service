# Copyright 2018-2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from unittest import mock

from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests import common
from odoo.tools.misc import mute_logger

_module_ns = "odoo.addons.project_role"
_project_role_class = _module_ns + ".models.project_role.ProjectRole"


class TestProjectRole(common.TransactionCase):
    def setUp(self):
        super().setUp()

        self.ResUsers = self.env["res.users"]
        self.Company = self.env["res.company"]
        self.Project = self.env["project.project"]
        self.Role = self.env["project.role"]
        self.Assignment = self.env["project.assignment"]
        self.company_id = self.env.user.company_id

    def test_create_assignment(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        project = self.Project.create({"name": "Project"})
        role = self.Role.create({"name": "Role"})
        self.Assignment.create(
            {"project_id": project.id, "role_id": role.id, "user_id": user.id}
        )

        self.assertEqual(self.Role.get_available_roles(user, project).ids, role.ids)

    def test_no_duplicate_assignment(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        project = self.Project.create({"name": "Project"})
        role = self.Role.create({"name": "Role"})
        self.Assignment.create(
            {"project_id": project.id, "role_id": role.id, "user_id": user.id}
        )

        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Assignment.create(
                {"project_id": project.id, "role_id": role.id, "user_id": user.id}
            )

    def test_restrict_assign(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        project = self.Project.create({"name": "Project"})
        role = self.Role.create({"name": "Role"})
        company_1 = self.Company.create({"name": "Company #1"})
        with mock.patch(
            _project_role_class + ".can_assign",
            return_value=False,
        ):
            with self.assertRaises(ValidationError):
                self.Assignment.create(
                    {"project_id": project.id, "role_id": role.id, "user_id": user.id}
                )
            with self.assertRaises(ValidationError):
                self.Assignment.create(
                    {"role_id": role.id, "user_id": user.id, "company_id": company_1.id}
                )
            with self.assertRaises(ValidationError):
                self.Assignment.create(
                    {
                        "company_id": self.company_id.id,
                        "role_id": role.id,
                        "user_id": user.id,
                    }
                )

    def test_multicompany_roles(self):
        company_1 = self.Company.create({"name": "Company #1"})
        self.Role.create({"name": "Role", "company_id": company_1.id})

        company_2 = self.Company.create({"name": "Company #2"})
        self.Role.create({"name": "Role", "company_id": company_2.id})

    def test_unique_crosscompany_role(self):
        self.Role.create({"name": "Role", "company_id": False})

        with self.assertRaises(ValidationError):
            self.Role.create({"name": "Role"})

    def test_nonconflicting_crosscompany_role(self):
        self.Role.create({"name": "Role"})

        with self.assertRaises(ValidationError):
            self.Role.create({"name": "Role", "company_id": False})

    def test_child_role(self):
        parent_role = self.Role.create({"name": "Parent Role"})
        child_role = self.Role.create(
            {"name": "Child Role", "parent_id": parent_role.id}
        )

        self.assertTrue(child_role.complete_name, "Parent Role / Child Role")

        with self.assertRaises(UserError):
            parent_role.parent_id = child_role

        child_role.active = False
        parent_role.active = False
        with self.assertRaises(ValidationError):
            child_role.active = True

    def test_companywide_assignments_1(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role = self.Role.create({"name": "Role"})

        self.Assignment.create({"role_id": role.id, "user_id": user.id})

        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Assignment.create({"role_id": role.id, "user_id": user.id})

    def test_companywide_assignments_2(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role_1 = self.Role.create({"name": "Role 1"})
        role_2 = self.Role.create({"name": "Role 2"})
        project = self.Project.create({"name": "Project"})

        self.Assignment.create({"role_id": role_1.id, "user_id": user.id})

        with self.assertRaises(ValidationError):
            self.Assignment.create(
                {"role_id": role_1.id, "user_id": user.id, "project_id": project.id}
            )

        self.Assignment.create({"role_id": role_2.id, "user_id": user.id})

    def test_companywide_assignments_3(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role_1 = self.Role.create({"name": "Role 1"})
        role_2 = self.Role.create({"name": "Role 2"})

        self.Assignment.create({"role_id": role_1.id, "user_id": user.id})

        self.Assignment.create({"role_id": role_2.id, "user_id": user.id})

    def test_crosscompany_assignments_1(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role = self.Role.create({"name": "Role", "company_id": False})

        self.Assignment.create(
            {"role_id": role.id, "user_id": user.id, "company_id": False}
        )

        with self.assertRaises(ValidationError):
            self.Assignment.with_context(
                company_id=self.company_id.id,
            ).create({"role_id": role.id, "user_id": user.id})

    def test_crosscompany_assignments_2(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role = self.Role.create({"name": "Role", "company_id": False})
        project = self.Project.create({"name": "Project"})

        self.Assignment.create(
            {"role_id": role.id, "user_id": user.id, "company_id": False}
        )

        with self.assertRaises(ValidationError):
            self.Assignment.with_context(
                company_id=self.company_id.id,
            ).create({"role_id": role.id, "user_id": user.id, "project_id": project.id})

    def test_crosscompany_assignments_3(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role_1 = self.Role.create({"name": "Role 1", "company_id": False})
        role_2 = self.Role.create({"name": "Role 2", "company_id": False})

        self.Assignment.create(
            {"role_id": role_1.id, "user_id": user.id, "company_id": False}
        )

        self.Assignment.with_context(
            company_id=self.company_id.id,
        ).create({"role_id": role_2.id, "user_id": user.id})

    def test_no_project(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        self.Role.create({"name": "Role"})
        self.assertFalse(self.Role.get_available_roles(user, False))

    def test_inherit_assignments(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role = self.Role.create({"name": "Role"})
        project = self.Project.create(
            {"name": "Project", "limit_role_to_assignments": True}
        )
        self.Assignment.create({"role_id": role.id, "user_id": user.id})

        self.assertEqual(self.Role.get_available_roles(user, project).ids, role.ids)

        project.inherit_assignments = False
        self.assertFalse(self.Role.get_available_roles(user, project))

    def test_limit_role_to_assignments(self):
        user = self.ResUsers.sudo().create(
            {
                "name": "User",
                "login": "user",
                "email": "user@example.com",
                "company_id": self.company_id.id,
            }
        )
        role = self.Role.create({"name": "Role"})
        project = self.Project.create({"name": "Project"})

        self.assertEqual(self.Role.get_available_roles(user, project).ids, role.ids)

        project.inherit_assignments = False
        self.assertEqual(self.Role.get_available_roles(user, project).ids, role.ids)

    def test_defaults(self):
        company = self.Company.create(
            {
                "name": "Company",
                "project_inherit_assignments": False,
                "project_limit_role_to_assignments": True,
            }
        )
        project = self.Project.create({"name": "Project", "company_id": company.id})
        self.Role.create({"name": "Role"})
        self.assertEqual(project.company_id.id, company.id)
        self.assertEqual(
            project.inherit_assignments, company.project_inherit_assignments
        )
        self.assertEqual(
            project.limit_role_to_assignments, company.project_limit_role_to_assignments
        )
