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
        # The URL of the https://github.com/hypothesis/via instance to
        # integrate with.
        'via_url': env_setting('VIA_URL', required=True),
        'jwt_secret': env_setting('JWT_SECRET', required=True),
        'google_client_id': env_setting('GOOGLE_CLIENT_ID'),
        'google_developer_key': env_setting('GOOGLE_DEVELOPER_KEY'),
        'google_app_id': env_setting('GOOGLE_APP_ID'),
        'lms_secret': env_setting('LMS_SECRET'),
        'hashed_pw': env_setting('HASHED_PW'),
        'salt': env_setting('SALT'),
        'username': env_setting('USERNAME'),
        # We need to use a randomly generated 16 byte array to encrypt secrets.
        # For now we will use the first 16 bytes of the lms_secret
        'aes_secret': env_setting('LMS_SECRET').encode('ascii')[0:16],

        # The OAuth 2.0 client_id and client_secret for authenticating to the h API.
        'h_client_id': env_setting('H_CLIENT_ID', required=True),
        'h_client_secret': env_setting('H_CLIENT_SECRET', required=True),

        # The authority that we'll create h users and groups in (e.g. "lms.hypothes.is").
        'h_authority': env_setting('H_AUTHORITY', required=True),

        # The base URL of the h API (e.g. "https://hypothes.is/api).
        'h_api_url': env_setting('H_API_URL', required=True),
    }

    database_url = env_setting('DATABASE_URL')
    if database_url:
        env_settings['sqlalchemy.url'] = database_url

    # Make sure that via_url doesn't end with a /.
    if env_settings['via_url'].endswith('/'):
        env_settings['via_url'] = env_settings['via_url'][:-1]

    # Make sure that h_api_url doesn't end with a /.
    if env_settings['h_api_url'].endswith('/'):
        env_settings['h_api_url'] = env_settings['h_api_url'][:-1]

    settings.update(env_settings)

    config = Configurator(settings=settings, root_factory='.resources.Root')

    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings['lms_secret'], callback=groupfinder,
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
