from copy import deepcopy

from sqlalchemy.ext.mutable import MutableDict


class ApplicationSettings(MutableDict):
    """Model for accessing and updating application settings."""

    def get(self, group, key):
        """
        Get a specific setting or None if it doesn't exist.

        :param group: The name of the group of settings
        :param key: The key in that group
        :return: The value or None
        """
        return super().get(group, {}).get(key)

    def set(self, group, key, value):
        """
        Set a specific setting in a group.

        :param group: The name of the group of settings
        :param key: The key in that group
        :param value: The value to set
        """
        super().setdefault(group, {})[key] = value

    def clone(self):
        return ApplicationSettings(deepcopy(self))

    def __repr__(self):
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __str__(self):
        return repr(self)
