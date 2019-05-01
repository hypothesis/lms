"""
Custom view predicates.

See:

https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#registering-thirdparty-predicates
"""


__all__ = ["FeatureFlagViewPredicate"]


class FeatureFlagViewPredicate:
    """The ``"feature_flag"`` view predicate."""

    def __init__(self, feature_flag, _config):
        """
        Initialize a view predicate that requires ``feature_flag``.

        :arg feature_flag: the feature flag that this predicate requires,
            for example ``"my_feature"``
        :type feature_flag: str
        :arg config: the Pyramid config object
        :type config: pyramid.config.Configurator
        """
        self._feature_flag = feature_flag

    def text(self):
        """
        Return a string describing the behavior of this predicate.

        Used by Pyramid in error messages.
        """
        return f"feature_flag = {self._feature_flag}"

    def phash(self):
        """
        Return a string uniquely identifying this predicate's name and value.

        Used by Pyramid for view configuration constraints handling.
        """
        return self.text()

    def __call__(self, context, request):
        """
        Return ``True`` if ``request`` matches this view predicate.

        Return ``False`` otherwise. Used by Pyramid during view lookup.
        """
        return request.feature(self._feature_flag)
