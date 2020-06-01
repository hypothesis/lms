class ApplicationSettings:
    """Model for accessing and updating application settings."""

    def __init__(self, data):
        self.data = data

    def get(self, group, key):
        """
        Get a specific settings or None if it doesn't exist.

        :param group: The name of the group of settings
        :param key: The key in that group
        :return: The value or None
        """
        return self.data.get(group, {}).get(key)

    def set(self, group, key, value):
        """
        Set a specific setting in a group.

        :param group: The name of the group of settings
        :param key: The key in that group
        :param value: The value to set
        """
        self.data.setdefault(group, {})[key] = value
