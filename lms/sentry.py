"""Sentry crash reporting integration."""


def includeme(config):
    config.add_settings(
        {
            "h_pyramid_sentry.retry_support": True,
            "h_pyramid_sentry.sqlalchemy_support": True,
        }
    )
    config.include("h_pyramid_sentry")
