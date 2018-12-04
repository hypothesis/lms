# -*- coding: utf-8 -*-

"""Configuration for the Pyramid application."""

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.config import aslist

from lms.security import groupfinder

from lms.config.settings import SettingError, env_setting


def configure(settings):
    """Return a Configurator for the Pyramid application."""
    # Settings from the config file are extended / overwritten by settings from
    # the environment.
    env_settings = {
        # The URL of the https://github.com/hypothesis/via instance to
        # integrate with.
        "via_url": env_setting("VIA_URL", required=True),
        "jwt_secret": env_setting("JWT_SECRET", required=True),
        "google_client_id": env_setting("GOOGLE_CLIENT_ID"),
        "google_developer_key": env_setting("GOOGLE_DEVELOPER_KEY"),
        "google_app_id": env_setting("GOOGLE_APP_ID"),
        "lms_secret": env_setting("LMS_SECRET"),
        "hashed_pw": env_setting("HASHED_PW"),
        "salt": env_setting("SALT"),
        "username": env_setting("USERNAME"),
        # We need to use a randomly generated 16 byte array to encrypt secrets.
        # For now we will use the first 16 bytes of the lms_secret
        "aes_secret": env_setting("LMS_SECRET", required=True),
        # The OAuth 2.0 client_id and client_secret for authenticating to the h API.
        "h_client_id": env_setting("H_CLIENT_ID", required=True),
        "h_client_secret": env_setting("H_CLIENT_SECRET", required=True),
        # The OAuth 2.0 client_id and client_secret for logging users in to h.
        "h_jwt_client_id": env_setting("H_JWT_CLIENT_ID", required=True),
        "h_jwt_client_secret": env_setting("H_JWT_CLIENT_SECRET", required=True),
        # The authority that we'll create h users and groups in (e.g. "lms.hypothes.is").
        "h_authority": env_setting("H_AUTHORITY", required=True),
        # The base URL of the h API (e.g. "https://hypothes.is/api).
        "h_api_url": env_setting("H_API_URL", required=True),
        # The list of `oauth_consumer_key`s of the application instances for
        # which the automatic user and group provisioning features are disabled.
        "no_auto_provisioning": env_setting("NO_AUTO_PROVISIONING", default=""),
        # The postMessage origins from which to accept RPC requests.
        "rpc_allowed_origins": env_setting("RPC_ALLOWED_ORIGINS", required=True),
    }

    database_url = env_setting("DATABASE_URL")
    if database_url:
        env_settings["sqlalchemy.url"] = database_url

    env_settings["via_url"] = _append_trailing_slash(env_settings["via_url"])
    env_settings["h_api_url"] = _append_trailing_slash(env_settings["h_api_url"])

    try:
        env_settings["aes_secret"] = env_settings["aes_secret"].encode("ascii")[0:16]
    except UnicodeEncodeError:
        raise SettingError("LMS_SECRET must contain only ASCII characters")

    env_settings["no_auto_provisioning"] = aslist(env_settings["no_auto_provisioning"])
    env_settings["rpc_allowed_origins"] = aslist(env_settings["rpc_allowed_origins"])

    settings.update(env_settings)

    config = Configurator(settings=settings, root_factory=".resources.Root")

    # Security policies
    authn_policy = AuthTktAuthenticationPolicy(
        settings["lms_secret"], callback=groupfinder, hashalg="sha512"
    )
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    return config


def _append_trailing_slash(s):  # pylint: disable=invalid-name
    """
    Return ``s`` with a trailing ``"/"`` appended.

    If ``s`` already ends with a trailing ``"/"`` it'll be returned unmodified.
    """
    if not s.endswith("/"):
        s = s + "/"
    return s


__all__ = ("SettingError", "configure", "env_setting")
