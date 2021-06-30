"""Private helpers for view predicates."""
from abc import ABCMeta, abstractmethod

__all__ = ["Base"]


class Base(metaclass=ABCMeta):
    """Abstract base class for custom view predicate classes."""

    def __init__(self, value, config):
        self.value = value
        self.config = config

    def text(self):
        """
        Return a string describing the behavior of this predicate.

        Used by Pyramid in error messages.
        """
        return f"{self.name} = {self.value}"

    def phash(self):
        """
        Return a string uniquely identifying this predicate's name and value.

        Used by Pyramid for view configuration constraints handling.
        """
        return self.text()

    @property
    @abstractmethod
    def name(self):
        """
        Return the name of this predicate.

        This is the string that is used as a keyword argument to Pyramid's
        ``@view_config()`` in order to use this predicate on a view. It's also
        used by ``text()`` and ``phash()``.
        """

    @abstractmethod
    def __call__(self, context, request):
        """Return ``True`` if ``request`` matches this predicate."""
