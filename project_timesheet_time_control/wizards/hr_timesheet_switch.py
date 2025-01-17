# Copyright 2019 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class HrTimesheetSwitch(models.TransientModel):
    _name = "hr.timesheet.switch"
    _description = "Helper to quickly switch between timesheet lines"

    def _domain_project_id(self):
        domain = [("allow_timesheets", "=", True)]
        if not self.env.user.has_group("hr_timesheet.group_timesheet_manager"):
            return expression.AND(
                [
                    domain,
                    [
                        "|",
                        ("privacy_visibility", "!=", "followers"),
                        ("message_partner_ids", "in", [self.env.user.partner_id.id]),
                    ],
                ]
            )
        return domain

    analytic_line_id = fields.Many2one(
        comodel_name="account.analytic.line", string="Origin line"
    )
    name = fields.Char(string="Description", required=True)
    date_time = fields.Datetime(
        string="Start Time", default=fields.Datetime.now, required=True
    )
    date_time_end = fields.Datetime(string="End Time")
    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Task",
        compute="_compute_task_id",
        store=True,
        readonly=False,
        index=True,
        domain="""
            [
                ('company_id', '=', company_id),
                ('project_id.allow_timesheets', '=', True),
                ('project_id', '=?', project_id)
            ]
        """,
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
        compute="_compute_project_id",
        store=True,
        readonly=False,
        domain=_domain_project_id,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    running_timer_id = fields.Many2one(
        comodel_name="account.analytic.line",
        string="Previous timer",
        ondelete="cascade",
        readonly=True,
        default=lambda self: self._default_running_timer_id(),
        help="This timer is running and will be stopped",
    )
    running_timer_start = fields.Datetime(
        string="Previous timer start",
        related="running_timer_id.date_time",
        readonly=True,
    )
    running_timer_duration = fields.Float(
        string="Previous timer duration",
        compute="_compute_running_timer_duration",
        help="When the previous timer is stopped, it will save this duration.",
    )

    @api.depends("task_id", "task_id.project_id")
    def _compute_project_id(self):
        for line in self.filtered(lambda line: not line.project_id):
            line.project_id = line.task_id.project_id

    @api.depends("project_id")
    def _compute_task_id(self):
        for line in self.filtered(lambda line: not line.project_id):
            line.task_id = False

    @api.model
    def _default_running_timer_id(self, employee=None):
        """Obtain running timer."""
        employee = employee or self.env.user.employee_ids
        # Find running work
        running = self.env["account.analytic.line"].search(
            [
                ("date_time", "!=", False),
                ("employee_id", "in", employee.ids),
                ("id", "not in", self.env.context.get("resuming_lines", [])),
                ("project_id", "!=", False),
                ("unit_amount", "=", 0),
            ]
        )
        if len(running) > 1:
            raise UserError(
                _(
                    "%d running timers found. Cannot know which one to stop. "
                    "Please stop them manually."
                )
                % len(running)
            )
        return running

    @api.depends("date_time", "running_timer_id")
    def _compute_running_timer_duration(self):
        """Compute duration of running timer when stopped."""
        for one in self:
            one.running_timer_duration = 0.0
            if one.running_timer_id:
                one.running_timer_duration = one.running_timer_id._duration(
                    one.running_timer_id.date_time,
                    one.date_time,
                )

    @api.model
    def _closest_suggestion(self):
        """Find most similar account.analytic.line record."""
        context = self.env.context
        model = "account.analytic.line"
        domain = [("employee_id", "in", self.env.user.employee_ids.ids)]
        if context.get("active_model") == model:
            return self.env[model].browse(context["active_id"])
        elif context.get("active_model") == "project.task":
            domain.append(("task_id", "=", context["active_id"]))
        elif context.get("active_model") == "project.project":
            domain += [
                ("project_id", "=", context["active_id"]),
                ("task_id", "=", False),
            ]
        else:
            return self.env[model]
        return self.env["account.analytic.line"].search(
            domain,
            order="date_time DESC",
            limit=1,
        )

    def _prepare_default_values(self, account_analytic_line):
        return {
            "analytic_line_id": account_analytic_line.id,
            "name": account_analytic_line.name,
            "project_id": account_analytic_line.project_id.id,
            "task_id": account_analytic_line.task_id.id,
        }

    @api.model
    def default_get(self, fields_list):
        """Return defaults depending on the context where it is called."""
        result = super().default_get(fields_list)
        inherited = self._closest_suggestion()
        if inherited:
            result.update(self._prepare_default_values(inherited))
        return result

    def _prepare_copy_values(self, record):
        """Return the values that will be overwritten in new timesheet entry."""
        return {
            "name": record.name,
            "date_time": record.date_time,
            "date_time_end": record.date_time_end,
            "project_id": record.project_id.id,
            "task_id": record.task_id.id,
            "unit_amount": 0,
        }

    def action_switch(self):
        """Stop old timer, start new one."""
        self.ensure_one()
        # Stop old timer
        self.with_context(
            resuming_lines=self.ids,
            stop_dt=self.date_time,
        ).running_timer_id.button_end_work()
        # Start new timer
        if self.analytic_line_id:
            new = self.analytic_line_id.copy(self._prepare_copy_values(self))
        else:
            fields = self.env["account.analytic.line"]._fields.keys()
            vals = self.env["account.analytic.line"].default_get(fields)
            vals.update(self._prepare_copy_values(self))
            new = self.env["account.analytic.line"].create(vals)
        # Display created timer record if requested
        if self.env.context.get("show_created_timer"):
            form_view = self.env.ref("hr_timesheet.hr_timesheet_line_form")
            return {
                "res_id": new.id,
                "res_model": new._name,
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "view_type": "form",
                "views": [(form_view.id, "form")],
            }
