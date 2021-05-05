"""Sentry crash reporting integration."""
from lms.services import ProxyAPIAccessTokenError


def filter_proxy_api_access_token_error(event):
    """Filter out all ProxyAPIAccessTokenError's."""
    return isinstance(event.exception, ProxyAPIAccessTokenError)


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.filters": [filter_proxy_api_access_token_error],
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
        }
    )
    config.include("h_pyramid_sentry")
