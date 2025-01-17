# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(env):
    """Put the date with 00:00:00 as the date_time for the line."""
    env.cr.execute(
        """UPDATE account_analytic_line
        SET date_time = to_timestamp(date || ' 00:00:00',
                                     'YYYY/MM/DD HH24:MI:SS')
        WHERE date(date_time) != date
        """
    )
