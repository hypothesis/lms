"""Subscribers for setting up the template environment."""
from pyramid.events import subscriber
from pyramid.events import BeforeRender

from lms.validation import BearerTokenSchema


__all__ = []


@subscriber(BeforeRender)
def _add_js_config(event):
    """
    Add the JavaScript config object to the template environment.

    A template renders this into the HTML page as a JSON object. The object
    contains general config settings used by the app's JavaScript code.
    """
    request = event["request"]

    event["js_config"] = {"urls": {"test_xhr": request.route_url("test_xhr")}}

    if request.lti_user:
        event["js_config"]["authorization_param"] = BearerTokenSchema(
            request
        ).authorization_param(request.lti_user)
