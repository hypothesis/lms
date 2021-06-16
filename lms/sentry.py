"""Sentry crash reporting integration."""
from lms.services import OAuth2TokenError


def filter_oauth2_token_error(event):
    """Filter out all OAuth2TokenError exceptions."""
    return isinstance(event.exception, OAuth2TokenError)


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.filters": [filter_oauth2_token_error],
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
        }
    )
    config.include("h_pyramid_sentry")
