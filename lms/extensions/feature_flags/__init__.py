"""
Feature flags Pyramid extension.

A feature flags Pyramid extension that supports reading feature flags from
multiple sources including:

- The config file
- Environment variables
- URL query string parameters
- Custom providers (you could add providers for reading feature flags from a
  cookie, the database, a feature flags microservice queried over HTTPS, ...)

Usage
=====

First include the extension in your app's configuration::

    config.include("lms.extensions.feature_flags")

This adds a ``request.feature(feature_flag_name)`` method that you can use to
query whether a given feature flag is active or not for the request. For
example::

  if request.feature("my_feature"):
      ...
  else:
      ...

Behind the scenes an ordered list of "feature flag providers" are queried that
consult different sources to see if the feature flag has been enabled or
disabled.

By default no sources are consulted and ``request.feature()`` always returns
``False``. You have to explicitly add the sources you want, in the order you
want, by calling ``config.add_feature_flag_provider()`` or
``add_feature_flag_providers()``.  For example::

    config.add_feature_flag_providers(
        "lms.extensions.feature_flags.config_file_provider",
        "lms.extensions.feature_flags.envvar_provider",
        "lms.extensions.feature_flags.query_string_provider",
    )

Provider Ordering
=================

Providers are called in the order in which they were added.  The *last*
provider to return ``True`` or ``False`` (rather than ``None``) overrides all
other providers, so the order in which the providers are added matters.

Builtin Providers
=================

``config_file_provider``
------------------------

Enable or disable feature flags in the app's config file.

Usage::

    config.add_feature_flag_provider("lms.extensions.feature_flags.config_file_provider")

To enable or disable feature flags in your app's config file add
``feature_flags.* = true|false`` lines to the file, one line per feature flag.
For example::

    [app:main]
    feature_flags.foo = true
    feature_flags.bar = false

``envvar_provider``
-------------------

Enable or disable feature flags using environment variables.

Usage::

    config.add_feature_flag_provider("lms.extensions.feature_flags.envvar_provider")

To enable or disable feature flags add ``FEATURE_FLAG_*=true|false``
environment variables, one envvar per feature flag. For example::

    export FEATURE_FLAG_FOO=true
    export FEATURE_FLAG_BAR=false

``query_string_provider``
-------------------------

Enable or disable feature flags using URL query string parameters.

Usage::

    config.add_feature_flag_provider("lms.extensions.feature_flags.query_string_provider")

To enable or disable feature flags add ``?feature_flags.foo=true|false``
parameters to the query string. For example::

    https://example.com/some/page?feature_flags.foo=true&feature_flag.bar=false

Custom Providers
================

You can write your own providers and add them by passing them to
``config.add_feature_flag_provider()`` in the same way as you would add one of
the builtin providers.  Each provider must be a callable that takes the request
as its first argument and the feature flag name (a string) as it second
argument and returns ``False`` if the flag has been explicitly disabled by its
source, ``True`` if it has been enabled, or ``None`` if the feature flag isn't
set by that source. For example::

    def hardcoded_provider(request, feature_flag_name):
        if feature_flag_name == "enabled_feature_flag":
            return True
        elif feature_flag_name == "disabled_feature_flag":
            return False
"""
from ._exceptions import SettingError
from ._feature_flags import FeatureFlags
from ._providers import config_file_provider  # noqa
from ._providers import envvar_provider  # noqa
from ._providers import query_string_provider  # noqa
from ._providers import cookie_provider  # noqa


__all__ = ["SettingError"]


def includeme(config):
    config.include("lms.extensions.feature_flags._routes")
    config.add_static_view(
        name="feature-flags-static", path="lms.extensions.feature_flags:_static"
    )

    # The singleton FeatureFlags instance for the entire app.
    feature_flags = FeatureFlags()

    def feature(request, feature_flag_name):
        """
        Adapt feature_flags.flag_is_active() to be used as a request method.

        This enables things to call request.feature("my_feature") and it'll
        call feature_flags.flag_is_active("my_feature").
        """
        return feature_flags.flag_is_active(request, feature_flag_name)

    def add_feature_flag_provider(_config, feature_flag_provider):
        """
        Adapt feature_flags.add_provider().

        Adapt feature_flags.add_provider() to enable it to be used as a Pyramid
        config directive.

        This enables things to call
        config.add_feature_flag_provider(my_provider) and it'll call
        feature_flags.add_provider(my_provider).
        """
        return feature_flags.add_provider(config.maybe_dotted(feature_flag_provider))

    def add_feature_flag_providers(_config, *providers):
        """Adapt feature_flags.add_providers()."""
        providers = [config.maybe_dotted(provider) for provider in providers]
        return feature_flags.add_providers(*providers)

    # Register the Pyramid request method and config directive. These are this
    # extension's public API.
    config.add_request_method(feature)
    config.add_directive(
        "add_feature_flag_provider", add_feature_flag_provider, action_wrap=False
    )
    config.add_directive(
        "add_feature_flag_providers", add_feature_flag_providers, action_wrap=False
    )
