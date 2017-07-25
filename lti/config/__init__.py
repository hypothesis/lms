# -*- coding: utf-8 -*-

"""Configuration for the Pyramid application."""

from __future__ import unicode_literals

from pyramid.config import Configurator

from lti.config.settings import (
    SettingError,
    env_setting,
)


def configure():
    """Return a Configurator for the Pyramid application."""
    return Configurator(settings={
        'lti_server': env_setting('LTI_SERVER'),
        'lti_credentials_url': env_setting('LTI_CREDENTIALS_URL'),
    })


__all__ = (
    'SettingError',
    'configure',
)
