# Copyright 2018, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import functools
import logging
from hashlib import sha256
from hmac import HMAC, compare_digest

from odoo import http
from odoo.http import request
from odoo.tools import consteq

_logger = logging.getLogger(__name__)


def token_authorization(function):
    """Decorator for controllers with token authorization.
    it allows only requests with X-Gitlab-Token or X-Hub-Signature-256 header present.

    Will returns an unsuccessful response whenever the token
    is invalid.
    """

    @functools.wraps(function)
    def wrapper(self, *args, **kw):
        headers = request.httprequest.headers
        gitlab_token = headers.get("X-Gitlab-Token")
        github_token = headers.get("X-Hub-Signature-256")
        token = request.env["ir.config_parameter"].sudo().get_param("webhook_gitlab.authorization_token")
        if github_token:
            expected_token = HMAC(
                key=token.encode("utf-8"),
                msg=request.httprequest.data,
                digestmod=sha256,
            ).hexdigest()
            authorization = compare_digest(github_token.split("sha256=")[-1].strip(), expected_token)
        elif gitlab_token:
            authorization = consteq(gitlab_token, token)
        if not authorization:
            _logger.warning("Token is not the expected")
            return False
        return function(self, *args, **kw)

    return wrapper


class WebhookGitlab(http.Controller):
    @http.route("/webhook_gitlab/webhook/", type="json", auth="public", csrf=False)
    @token_authorization
    def _process_webhook(self):
        """Receive the request from Gitlab/Github and invoke functions based on
        'object_kind', then it calls the function with the name
        _process_<object_kind>
        """
        event = request.get_json_data()
        request_obj = request.env["git.request"]
        try:
            if event.get("object_kind"):
                func = getattr(request_obj.with_delay(), "_process_%s" % event["object_kind"])
            else:
                func = request_obj.with_delay()._process_pull_request
        except AttributeError as error:
            _logger.warning(error)
            return error
        return func(event)
