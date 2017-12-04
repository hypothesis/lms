# -*- coding: utf-8 -*-

"""Configuration for the Pyramid application."""

from __future__ import unicode_literals

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

from lms.security import groupfinder

from lms.config.settings import (
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
        'lms_server': env_setting('LMS_SERVER', required=True),
        'lms_credentials_url': env_setting('LMS_CREDENTIALS_URL',
                                           required=True),
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

    config = Configurator(settings=settings, root_factory='.resources.Root')

    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings['lms.secret'], callback=groupfinder,
        hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    return config


__all__ = (
    'SettingError',
    'configure',
    'env_setting'
)
