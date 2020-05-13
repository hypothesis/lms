"""
Builtin feature flag providers.

See the :mod:`~lms.extensions.feature_flags` package for the public API
documentation for these functions.
"""
import os

from ._helpers import FeatureFlagsCookieHelper, as_tristate

__all__ = [
    "config_file_provider",
    "envvar_provider",
    "cookie_provider",
    "query_string_provider",
]


def config_file_provider(request, feature_flag_name):
    """
    Return whether the feature flag is set in the config file.

    Return ``True`` or ``False`` if the given feature flag is enabled or
    disabled in the config file, or ``None`` if the config file doesn't mention
    the given feature flag.
    """
    return as_tristate(
        request.registry.settings.get(f"feature_flags.{feature_flag_name}")
    )


def envvar_provider(_request, feature_flag_name):
    """
    Return whether the feature flag is set in the environment.

    Return ``True`` or ``False`` if the given feature flag is enabled or
    disabled by an environment variable, or ``None`` if there's no environment
    variable for this feature flag.
    """
    return as_tristate(os.environ.get(f"FEATURE_FLAG_{feature_flag_name.upper()}"))


def cookie_provider(request, feature_flag_name):
    return FeatureFlagsCookieHelper(request).get(feature_flag_name)


def query_string_provider(request, feature_flag_name):
    """
    Return whether the feature flag is set in the URL's query string.

    Return ``True`` or ``False`` if the given feature flag is enabled or
    disabled by a query string parameter, or ``None`` if there's no query
    string parameter for this feature flag.
    """

    return as_tristate(request.GET.get(f"feature_flags.{feature_flag_name}"))
