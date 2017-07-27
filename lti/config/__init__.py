# -*- coding: utf-8 -*-

"""Configuration for the Pyramid application."""

from __future__ import unicode_literals

from pyramid.config import Configurator

from lti.config.settings import (
    SettingError,
    env_setting,
)


def configure(settings=None):
    """Return a Configurator for the Pyramid application."""
    if settings is None:
        settings = {}

    # Settings from the config file are extended / overwritten by settings from
    # the environment.
    settings.update(dict(
        lti_server=env_setting('LTI_SERVER'),
        lti_credentials_url=env_setting('LTI_CREDENTIALS_URL'),
    ))

    return Configurator(settings=settings)


__all__ = (
    'SettingError',
    'configure',
)
