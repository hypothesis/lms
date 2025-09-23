"""Sentry crash reporting integration."""

from sentry_sdk.types import Hint, Log

from lms._version import get_version


def before_send_log(log: Log, _hint: Hint) -> Log | None:
    """Filter out log messages that we don't want to send to Sentry Logs."""

    if log.get("attributes", {}).get("logger.name") == "gunicorn.access":
        return None

    return log


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.celery_support": True,
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
            "h_pyramid_sentry.init.enable_logs": True,
            "h_pyramid_sentry.init.before_send_log": before_send_log,
        }
    )
    config.include("h_pyramid_sentry")
