.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

==================
Webhook for Gitlab
==================

The prurpose of this module is to receive Gitab Webhooks to make different actions in Odoo.

List of Functions
=================

#. Post a message in a task or ticket if the name of a new Merge Request contains keywords related to a ticket or task ID.
#. Post a message in Gitlab Merge Request that contains a link to Odoo ticket or task.

Configuration
=============

To configure this module, you need to:

#. Go to System Parameters
#. Set a token in 'webhook_gitlab.authorization_token' parameter.
#. Define url of the Odoo instance as 'web.base.url' parameter.
#. Define url of the Gitlab instance as 'webhook_gitlab.gitlab_token' + url parameter.
#. Obtain personal token from Gitlab and define it as 'webhook_gitlab.gitlab_token' parameter.

In Gitlab:

#. Go to the repository url you want to integrate.
#. Got to Settings/Integrations.
#. Define URL http://<your domain>/webhook_gitlab/webhook/
#. Define Token (This must be the same configured in webhook_gitlab.authorization_token parameter).
#. Select the Trigger events that you want to process.

Usage
=====

To use this module, you need to:

#. Use Gitlab


Credits
=======

Contributors
------------

* Alan Ramos <alan.ramos@jarsa.com.mx>

Maintainer
----------

.. image:: http://www.jarsa.com.mx/logo.png
   :alt: Jarsa
   :target: http://www.jarsa.com.mx

This module is maintained by Jarsa
