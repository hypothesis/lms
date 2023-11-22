"""Configuration for the Pyramid application."""

import os
from dataclasses import dataclass
from typing import Callable, List, Optional

from pyramid.config import Configurator
from pyramid.config import aslist as _aslist
from pyramid.settings import asbool


def aslist(value: Optional[str]) -> List[str]:
    # pyramid's aslist doesn't accept None values
    # coerce those to "" which becomes an empty list.
    return _aslist("" if value is None else value)


class SettingError(Exception):
    pass


def _append_trailing_slash(string):
    """Append a slash to a string if none was there before."""

    return string if string.endswith("/") else string + "/"


def _aes_to_16_chars(string):
    """Get 16 ascii bytes from the provided string."""

    try:
        return string.encode("ascii")[0:16] if string else None
    except UnicodeEncodeError as err:
        raise SettingError("LMS_SECRET must contain only ASCII characters") from err


@dataclass(frozen=True)
class _Setting:
    """The properties of a setting and how to read it."""

    name: str
    read_from: str = None
    value_mapper: Callable = None

    def __post_init__(self):
        if not self.read_from:
            object.__setattr__(self, "read_from", self.name)


SETTINGS = (
    # List of users that are ADMINS in the admin pages
    _Setting("admin_users", value_mapper=aslist),
    _Setting("database_url"),
    _Setting("h_fdw_database_url"),
    _Setting("fdw_users", value_mapper=aslist),
    # Whether we're in "dev" mode (as opposed to QA, production or tests).
    _Setting("dev", value_mapper=asbool),
    # The URL of the https://github.com/hypothesis/via instance to
    # integrate with.
    _Setting("via_url", value_mapper=_append_trailing_slash),
    _Setting("via_secret"),
    _Setting("jwt_secret"),
    _Setting("google_client_id"),
    _Setting("google_developer_key"),
    _Setting("onedrive_client_id"),
    _Setting("lms_secret"),
    # We need to use a randomly generated 16 byte array to encrypt secrets.
    # For now we will use the first 16 bytes of the lms_secret
    _Setting("aes_secret", read_from="lms_secret", value_mapper=_aes_to_16_chars),
    # The secret string that's used to sign the session cookie.
    # This needs to be a 64-byte, securely generated random string.
    # For example you can generate one using Python 3 on the command line
    # like this:
    #     python3 -c 'import secrets; print(secrets.token_hex(nbytes=64))'
    _Setting("session_cookie_secret"),
    # The OAuth 2.0 client_id and client_secret for authenticating to the h API.
    _Setting("h_client_id"),
    _Setting("h_client_secret"),
    # The OAuth 2.0 client_id and client_secret for logging users in to h.
    _Setting("h_jwt_client_id"),
    _Setting("h_jwt_client_secret"),
    # The authority that we'll create h users and groups in (e.g. "lms.hypothes.is").
    _Setting("h_authority"),
    # The public base URL of the h API (e.g. "https://hypothes.is/api).
    _Setting("h_api_url_public", value_mapper=_append_trailing_slash),
    # A private (within-VPC) URL for the same h API. Faster and more secure
    # than the public one. This is used for internal server-to-server
    # comms.
    _Setting("h_api_url_private", value_mapper=_append_trailing_slash),
    # The postMessage origins from which to accept RPC requests.
    _Setting("rpc_allowed_origins", value_mapper=aslist),
    # The secret string that's used to sign the feature flags cookie.
    # For example you can generate one using Python 3 on the command line
    # like this:
    #     python3 -c 'import secrets; print(secrets.token_hex())'
    _Setting("feature_flags_cookie_secret"),
    # The list of feature flags that are allowed to be set in the feature flags cookie.
    _Setting("feature_flags_allowed_in_cookie"),
    # The secret string that's used to sign the OAuth 2 state param.
    # For example, you can generate one using Python 3 on the command line
    # like this:
    #     python3 -c 'import secrets; print(secrets.token_hex())'
    _Setting("oauth2_state_secret"),
    _Setting("vitalsource_api_key"),
    _Setting("admin_auth_google_client_id"),
    _Setting("admin_auth_google_client_secret"),
    _Setting("blackboard_api_client_id"),
    _Setting("blackboard_api_client_secret"),
    _Setting("jstor_api_url"),
    _Setting("jstor_api_secret"),
    _Setting("youtube_api_key"),
    _Setting("disable_key_rotation", value_mapper=asbool),
    _Setting("mailchimp_api_key"),
    _Setting("mailchimp_digests_subaccount"),
    _Setting("mailchimp_digests_email"),
    _Setting("mailchimp_digests_name"),
)


def configure(settings):
    """Return a Configurator for the Pyramid application."""

    for setting in SETTINGS:
        try:
            value = os.environ[setting.read_from.upper()]
        except KeyError:
            value = settings.get(setting.read_from)

        if setting.value_mapper:
            value = setting.value_mapper(value)

        settings[setting.name] = value

    return Configurator(settings=settings)
