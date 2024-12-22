# Copyright 2020, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from urllib.parse import urljoin

import gitlab  # pylint: disable=W7935
from github import Github

from odoo import _, api, fields, models


class GitRequest(models.Model):
    _name = "git.request"
    _description = "Information for Pull/Merge Requests"

    task_id = fields.Many2one("project.task", ondelete="cascade")
    id_request = fields.Integer(string="Request ID", help="Technical field used to track the merge request id")
    id_project = fields.Integer(
        string="Project ID",
        help="Technical field used to track the project id in Gitlab",
    )
    name = fields.Char(string="Title")
    wip = fields.Boolean(string="WIP")
    branch = fields.Char()
    last_commit = fields.Char()
    approved = fields.Boolean()
    state = fields.Selection(
        [
            ("opened", "Opened"),
            ("merged", "Merged"),
            ("closed", "Closed"),
            ("locked", "Locked"),
        ]
    )
    ci_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("skipped", "Skipped"),
            ("canceled", "Canceled"),
            ("unknown", "Unknown"),
        ],
        default="pending",
        string="CI Status",
    )
    url = fields.Char()
    user_id = fields.Many2one("res.users", string="Created by User")

    def open_merge_request(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.url,
        }

    @api.model_create_multi
    def create(self, vals_list):
        rec = super().create(vals_list)
        rec.assing_tags()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self.assing_tags()
        return res

    def assing_tags(self):
        for rec in self:
            tags = []
            record = rec.task_id
            tag_model = record.tag_ids._name
            current_tags = self.env[tag_model]
            current_tags |= record.tag_ids.filtered(lambda t: t.name.startswith("MR:") or t.name.startswith("CI:"))
            for tag in current_tags:
                tags.append((3, tag.id, 0))
            # Create prefix to have a base to get the external ID.
            # Possible values of prefix:
            # 'webhook_gitlab.project_tags_'
            prefix = "webhook_gitlab." + tag_model.replace(".", "_") + "_"
            # Get CI status tag.
            tags.append((4, self.env.ref(prefix + rec.ci_status).id, 0))
            # Get MR state tag.
            tags.append((4, self.env.ref(prefix + rec.state).id, 0))
            if rec.approved:
                tags.append((4, self.env.ref(prefix + "approved").id, 0))
            else:
                tags.append((3, self.env.ref(prefix + "approved").id, 0))
            if rec.wip:
                tags.append((4, self.env.ref(prefix + "wip").id, 0))
            else:
                tags.append((3, self.env.ref(prefix + "wip").id, 0))
            record.write(
                {
                    "tag_ids": tags,
                }
            )

    @api.model
    def _get_record_type_and_id(self, title):
        """Searches in the title of the MR for the task ID with the
        correct format and returns the type of record and id if it can find it.

        :param title: Title of the MR
        :type: string
        :return: Dictionary with the type of record and ID obtained from the
        title or False if the title does not contain a correct format.
        :rtype: dictionary or boolean
        """
        exp = r"^(.*[ \(\[\<])?(?P<type>t(ask)?)#?(?P<id>\d+)([\)\]\>:=, \.,].*)?$"
        match = re.match(exp, title, re.IGNORECASE)
        if match:
            return match.groupdict()
        return False

    @api.model
    def _link_record(self, event, id_found):
        """Add link to GitLab to access Odoo task.
        Create the git.request related to task.
        """
        model = "project.task"
        rec_type = "task"
        record = self.env[model].sudo().browse(int(id_found["id"]))
        if not record:
            message = _(
                "The %(type)s #%(id)s cannot be found in Odoo.",
                type=rec_type,
                id=id_found["id"],
            )
            self._post_message(event, message)
            return False
        if event.get("object_kind"):
            project_id = event["project"]["id"]
            merge_request_id = event["object_attributes"]["iid"]
        else:
            project_id = event["repository"]["id"]
            merge_request_id = event["number"]
        git_request = self.sudo().search(
            [
                ("id_request", "=", merge_request_id),
                ("id_project", "=", project_id),
            ]
        )
        git_request_vals = self._prepare_git_request(record, event)
        if git_request:
            git_request.sudo().write(git_request_vals)
            return False
        git_request.sudo().create(git_request_vals)
        url = record._notify_get_action_link("view")
        message = _(
            "Linked to Odoo %(type)s [#%(id)s](%(url)s)",
            type=rec_type,
            id=record.id,
            url=url,
        )
        self._post_message(event, message)
        return True

    @api.model
    def _prepare_git_request(self, record, event):
        if event.get("object_kind"):
            vals = self._prepare_gilab_git_request(event)
        else:
            vals = self._prepare_github_git_request(event)
        if record._name == "project.task":
            vals["task_id"] = record.id
        return vals

    @api.model
    def _prepare_gilab_git_request(self, event):
        approved = False
        if event["object_attributes"]["action"] == "approved":
            approved = True
        user = self.env["res.users"].sudo().search([("gitlab_username", "=", event["user"]["username"])])
        return {
            "id_request": event["object_attributes"]["iid"],
            "id_project": event["project"]["id"],
            "name": event["object_attributes"]["title"],
            "wip": event["object_attributes"]["work_in_progress"],
            "state": event["object_attributes"]["state"],
            "approved": approved,
            "url": event["object_attributes"]["url"],
            "branch": event["object_attributes"]["source_branch"],
            "last_commit": event["object_attributes"]["last_commit"]["id"],
            "task_id": False,
            "user_id": user.id,
        }

    @api.model
    def _prepare_github_git_request(self, event):
        user = (
            self.env["res.users"]
            .sudo()
            .search(
                [
                    ("github_username", "=", event["pull_request"]["user"]["login"]),
                ]
            )
        )
        map_state = {
            "open": "opened",
            "closed": "closed",
            "merged": "merged",
        }
        return {
            "id_request": event["number"],
            "id_project": event["repository"]["id"],
            "name": event["pull_request"]["title"],
            "state": map_state[event["pull_request"]["state"]],
            "url": event["pull_request"]["html_url"],
            "branch": event["pull_request"]["head"]["ref"],
            "last_commit": event["pull_request"]["head"]["sha"],
            "task_id": False,
            "user_id": user.id,
        }

    @api.model
    def _process_merge_request(self, event):
        """Post messages in project.task based on the
        title of the Merge Request.
        The title must contain the type of registry and the ID preceded by a #
        sign.

        Ex. [IMP] webhook_gitlab: new module task#1234
        """
        title = event["object_attributes"]["title"]
        id_found = self._get_record_type_and_id(title)
        if not id_found:
            message = self.env["ir.qweb"]._render("webhook_gitlab.gitlab_id_not_in_title")
            self._post_message(event, message)
            return False
        return self._link_record(event, id_found)

    @api.model
    def _process_pull_request(self, event):
        """Post messages in project.task based on the
        title of the Pull Request.
        The title must contain the type of registry and the ID preceded by a #
        sign.

        Ex. [IMP] webhook_gitlab: new module task#1234
        """
        title = event["pull_request"]["title"]
        id_found = self._get_record_type_and_id(title)
        if not id_found:
            message = self.env["ir.qweb"]._render("webhook_gitlab.gitlab_id_not_in_title")
            self._post_message(event, message)
            return False
        return self._link_record(event, id_found)

    @api.model
    def _process_pipeline(self, event):
        """Process pipeline status and update git.request in task.
        The title must contain the type of registry and the ID preceded by a #
        sign.

        Ex. [IMP] webhook_gitlab: new module task #1234
        """
        git_request = (
            self.env["git.request"]
            .sudo()
            .search(
                [
                    ("branch", "=", event["object_attributes"]["ref"]),
                    ("last_commit", "=", event["object_attributes"]["sha"]),
                ]
            )
        )

        if git_request:
            git_request.sudo().write(
                {
                    "ci_status": event["object_attributes"]["status"],
                }
            )
        return True

    @api.model
    def _connect_gitlab(self, event=None, url=None):
        """Connect to gitlab instance and return gitlab object"""
        if not url:
            url = event["project"]["web_url"]
        url = urljoin(url, "../..")
        token = self.env["ir.config_parameter"].sudo().get_param("webhook_gitlab.gitlab_token." + url)
        return gitlab.Gitlab(url, private_token=token)

    @api.model
    def _connect_github(self):
        """Connect to github instance and return github object"""
        token = self.env["ir.config_parameter"].sudo().get_param("webhook_gitlab.github_token")
        return Github(token)

    @api.model
    def _post_message(self, event, message):
        """Post a Message on Gitlab or Github"""
        if event.get("object_kind"):
            return self._post_gitlab_message(event, message)
        return self._post_github_message(event, message)

    @api.model
    def _post_github_message(self, event, message):
        """Post a message in the pull request of a project"""
        response = self._connect_github()
        repo = response.get_repo(event["repository"]["full_name"])
        pull = repo.get_pull(event["number"])
        pull.create_issue_comment(message)
        return True

    @api.model
    def _post_gitlab_message(self, event, message):
        """Post a message in the merge request of a project"""
        project_id = event["project"]["id"]
        merge_request_id = event["object_attributes"]["iid"]
        response = self._connect_gitlab(event)
        project = response.projects.get(project_id)
        merge_request = project.mergerequests.get(merge_request_id)
        merge_request.discussions.create({"body": message})
        return True
