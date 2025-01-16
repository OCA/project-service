# Copyright 2016 Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def pre_init_hook(env):
    """
    With this pre-init-hook we want to avoid error when creating the UNIQUE
    code constraint when the module is installed and before the post-init-hook
    is launched.
    """
    env.cr.execute("ALTER TABLE project_task ADD COLUMN code character varying;")
    env.cr.execute("UPDATE project_task SET code = id;")


def post_init_hook(env):
    """
    This post-init-hook will update all existing task assigning them the
    corresponding sequence code.
    """
    task_obj = env["project.task"]
    sequence_obj = env["ir.sequence"]
    tasks = task_obj.search([], order="id")
    for task_id in tasks.ids:
        env.cr.execute(
            "UPDATE project_task SET code = %s WHERE id = %s;",
            (
                sequence_obj.next_by_code("project.task"),
                task_id,
            ),
        )
