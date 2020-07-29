"""Sentry crash reporting integration."""
from lms.services import CanvasAPIAccessTokenError


def filter_canvas_api_access_token_error(event):
    """Filter out all CanvasAPIAccessTokenError's."""
    return isinstance(event.exception, CanvasAPIAccessTokenError)


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.init.traces_sample_rate": 0.25,
            "h_pyramid_sentry.init._experiments": {"auto_enabling_integrations": True},
            "h_pyramid_sentry.filters": [filter_canvas_api_access_token_error],
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
        }
    )
    config.include("h_pyramid_sentry")
