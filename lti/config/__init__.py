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
    env_settings = {
        'lti_server': env_setting('LTI_SERVER', required=True),
        'lti_credentials_url': env_setting('LTI_CREDENTIALS_URL',
                                           required=True),
        'lti_files_path': env_setting('LTI_FILES_PATH',
                                      default='./lti/static/pdfjs/viewer/web'),
        # The origin that this app should use when sending postMessage()
        # requests to the Hypothesis client (e.g. "https://hypothes.is" in prod
        # or "http://localhost:5000" in dev).
        'client_origin': env_setting('CLIENT_ORIGIN', required=True),

        # The URL of the https://github.com/hypothesis/via instance to
        # integrate with.
        'via_url': env_setting('VIA_URL', required=True),
    }

    database_url = env_setting('DATABASE_URL')
    if database_url:
        env_settings['sqlalchemy.url'] = database_url

    # Make sure that via_url doesn't end with a /.
    if env_settings['via_url'].endswith('/'):
        env_settings['via_url'] = env_settings['via_url'][:-1]

    settings.update(env_settings)

    return Configurator(settings=settings)


__all__ = (
    'SettingError',
    'configure',
)
