"""Subscribers for setting up the template environment."""
from pyramid.events import subscriber
from pyramid.events import BeforeRender


__all__ = []


@subscriber(BeforeRender)
def _add_js_config(event):
    """
    Add the JavaScript config object to the template environment.

    A template renders this into the HTML page as a JSON object. The object
    contains general config settings used by the app's JavaScript code.
    """
    event["js_config"] = {"urls": {}}
