"""Sentry crash reporting integration."""
from lms.services import CanvasAPIAccessTokenError


def filter_canvas_api_access_token_error(event):
    """Filter out all CanvasAPIAccessTokenError's."""
    return isinstance(event.exception, CanvasAPIAccessTokenError)


def includeme(config):
    config.add_settings(
        {"h_pyramid_sentry.filters": [filter_canvas_api_access_token_error]}
    )
    config.include("h_pyramid_sentry")
