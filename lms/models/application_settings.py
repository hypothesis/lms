class ApplicationSettings:
    """Model for accessing and updating application settings."""

    def __init__(self, data):
        self.data = data

    def get(self, group, key):
        """
        Return the "group.key" setting or None if it doesn't exist.

        :param group: The name of the group of settings
        :param key: The key of the setting in the group
        :return: The value of the setting or None
        """
        return self.data.get(group, {}).get(key)

    def set(self, group, key, value):
        """
        Set the "group.key" setting.

        :param group: The name of the group of settings
        :param key: The key of the setting in the group
        :param value: The new value for the setting
        """
        self.data.setdefault(group, {})[key] = value
