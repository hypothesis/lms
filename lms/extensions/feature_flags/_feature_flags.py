"""
Feature flags class.

This module exports a :class:`FeatureFlags` class with methods for adding
feature flag providers and for querying whether a feature flag is active for a
request.

The :class:`FeatureFlags` class is for internal use only. Outside code would
normally only access it indirectly via public methods like
``config.add_feature_flag_provider()`` and ``request.feature()``.
See the :mod:`~lms.extensions.feature_flags` package for documentation of this
public interface.
"""

__all__ = ["FeatureFlags"]


class FeatureFlags:
    """
    An aggregator for feature flags providers.

    Provides :meth:`add_provider()` for adding a feature flags
    provider, and :meth:`flag_is_active()` for querying all of the added
    providers to see whether a given feature flag is active for a request.

    :mod:`~lms.extensions.feature_flags` provides a public interface to these
    methods, see that package for documentation.
    """

    def __init__(self):
        self._providers = []

    def flag_is_active(self, request, feature_flag_name):
        """
        Return whether the feature flag is active for the request.

        Consult all added feature flag providers and return ``True`` if the
        given feature flag is active for the current request, ``False``
        otherwise. All feature flags are ``False`` by default (if no source
        toggles the feature flag either on or off, it will be off by default).
        """

        for provider in reversed(self._providers):
            enabled = provider(request, feature_flag_name)
            if enabled is not None:
                return enabled

        return False

    def add_providers(self, *providers):
        """Add a list of feature flag providers."""
        self._providers.extend(providers)
