"""
Functions for filtering out events we don't want to report to Sentry.

These are called by h-pyramid-sentry:
https://github.com/hypothesis/h-pyramid-sentry/
"""
from lms.services import CanvasAPIAccessTokenError


def filter_canvas_api_access_token_error(event):
    """Filter out all CanvasAPIAccessTokenError's."""
    return isinstance(event.exception, CanvasAPIAccessTokenError)


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.filters": [filter_canvas_api_access_token_error],
            "h_pyramid_sentry.retry_support": False,
        }
    )
    config.include("h_pyramid_sentry")
