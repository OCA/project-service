Forecast lines have the following data:

* Forecast hours: it is positive for resources (employees) and negative for
  things which consume time (project tasks, for instance)

* From and To date which are the beginning and ending of the period of the
  capacity

* Consolidated forecast: this is a computed field, which is computed as follows:

  * for costs (project tasks for instance) we take the absolute value of the
    forecast hours (so it is a positive number)

  * for resources (employee capacity for a period), we take the capacity and
    substract all the costs for that employee on the same period. So it will be
    positive if the employee still has some free time, and negative if he is
    overloaded with work.

  * this consolidated forecast is currently converted to days to ease
    readability of the forecast report


Objects creating forecast lines:

* employees with a forecast role will create forecast line with a positive
  capacity and type "confirmed" for each day on which they work. This
  information comes from their work calendar, and the different roles that are
  linked to the employee.

* draft sale orders (if enabled in the settings) will create forecast lines of
  type "forecast" for each sale order line having a product with a forecast
  role and start and end dates. The forecast hours are negative

* confirmed sale orders don't create forecast lines. This is handled by the
  tasks created at the confirmation of the sale order

* project tasks create forecast lines if they have a linked role and planned start/end
  dates. The type of the line will depend on the related project's stage. The
  `forecast_hours` field is based on the remaining time of the task, which is spread
  on the work days of the planned start and end date of the task. If the
  current date is in the middle of the planned duration of the task, it is used
  as the start date. If the planned end date is in the past the task does not
  generate forecast lines (and you need to fix your planning). In case multiple
  employees are assigned to the task the forecast is split equally between
  them.

* holiday requests create negative forecast lines with type "forecast" when
  they are pending manager validation.

* Validated holiday requests do not generate forecast lines, as they alter the
  work calendar of the employee: the employee will not have a positive line
  associated to his leave days.

The creation of forecast lines is done either in real time when some actions
are performed by the user (requesting leaves, updating the remaining time on a
project task, timesheeting) and also via a cron that runs on a daily basis. The
cron is required to cleanup lines related to dates in the past and to recompute
the lines related to project tasks by computing the ratio of remaing time on
the tasks on the remaining days, for tasks which are in progress. So, to start
using consolidated forecast report you first need to set everything mentioned
in Usage section. Then, probably run Forecast recomputation cron manually from
Scheduled Actions or wait till cron creates records.
