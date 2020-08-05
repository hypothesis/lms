"""Sentry crash reporting integration."""
from lms.services import BlackboardAPIAccessTokenError, CanvasAPIAccessTokenError


def filter_canvas_api_access_token_error(event):
    """Filter out all CanvasAPIAccessTokenError's."""
    return isinstance(event.exception, CanvasAPIAccessTokenError)


def filter_blackboard_api_access_token_error(event):
    return isinstance(event.exception, BlackboardAPIAccessTokenError)


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.filters": [filter_canvas_api_access_token_error],
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
        }
    )
    config.include("h_pyramid_sentry")
