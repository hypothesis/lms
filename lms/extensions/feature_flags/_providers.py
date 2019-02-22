"""
Builtin feature flag providers.

See the :mod:`~lms.extensions.feature_flags` package for the public API
documentation for these functions.
"""
import os

from pyramid.settings import asbool

__all__ = ["config_file_provider", "envvar_provider", "query_string_provider"]


def config_file_provider(request, feature_flag_name):
    """
    Return whether the feature flag is set in the config file.

    Return ``True`` or ``False`` if the given feature flag is enabled or
    disabled in the config file, or ``None`` if the config file doesn't mention
    the given feature flag.
    """
    setting_name = f"feature_flags.{feature_flag_name}"
    return _bool_or_none_from_dict(request.registry.settings, setting_name)


def envvar_provider(_request, feature_flag_name):
    """
    Return whether the feature flag is set in the environment.

    Return ``True`` or ``False`` if the given feature flag is enabled or
    disabled by an environment variable, or ``None`` if there's no environment
    variable for this feature flag.
    """
    key = "FEATURE_FLAG_{name}".format(name=feature_flag_name.upper())
    return _bool_or_none_from_dict(os.environ, key)


def query_string_provider(request, feature_flag_name):
    """
    Return whether the feature flag is set in the URL's query string.

    Return ``True`` or ``False`` if the given feature flag is enabled or
    disabled by a query string parameter, or ``None`` if there's no query
    string parameter for this feature flag.
    """
    key = f"feature_flags.{feature_flag_name}"
    return _bool_or_none_from_dict(request.GET, key)


def _bool_or_none_from_dict(dict_, key):
    result = dict_.get(key)

    if result is None:
        return None

    return asbool(result)
