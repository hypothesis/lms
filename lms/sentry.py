"""Sentry crash reporting integration."""

from lms._version import get_version


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
            "h_pyramid_sentry.init.release": get_version(),
        }
    )
    config.include("h_pyramid_sentry")
