"""Sentry crash reporting integration."""

from lms._version import get_version


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
            # Enable Sentry's "Releases" feature, see:
            # https://docs.sentry.io/platforms/python/configuration/options/#release
            #
            # h_pyramid_sentry passes any h_pyramid_sentry.init.* Pyramid settings
            # through to sentry_sdk.init(), see:
            # https://github.com/hypothesis/h-pyramid-sentry?tab=readme-ov-file#settings
            #
            # For the full list of options that sentry_sdk.init() supports see:
            # https://docs.sentry.io/platforms/python/configuration/options/
            "h_pyramid_sentry.init.release": get_version(),
        }
    )
    config.include("h_pyramid_sentry")
