This module allows to plan your resources using forecast lines.

For each employee of the company, the module will generate forecast line
records with a positive capacity based on their working time schedules. Then,
tasks assigned to employees will generate forecast lines with a negative
capacity which will "consume" the work time capacity of the employees.

The idea is that you can then see the work capacity and scheduled work of
people by summing the "forecasts" per time period. If you have more resources
(positive forecast) than work (negative forecast) you will have a positive net
sum. Otherwise you are in trouble and need to recruit or reschedule your
work. Another way to use the report is checking when the work capacity of a
department becomes positive (or high enough) in order to provide you potential
customers with an estimate of when a project would be able to start.

Forecast lines also come in two states "forecast" or "confirmed", depending on
whether the consumption is confirmed or not. For instance, holidays requests
and sales quotation lines create lines of type "forecast", whereas tasks for
project which are in a running state create lines with type "confirmed".

To get the best experience using the Forecast application you may want to install:

* project_forecast_line_holidays_public module which takes public holidays into
  account during forecast lines creation

* project_forecast_line_bokeh_chart module which improves the reports of
  project_forecast_line module by using the bokeh widget available in OCA/web
