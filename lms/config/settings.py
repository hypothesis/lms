"""Functions for reading config settings."""

import os


class SettingError(Exception):
    pass


class SettingGetter:  # pylint:disable=too-few-public-methods
    """Helper for getting values of settings from envvars or config file."""

    def __init__(self, settings):
        """
        Initialize a new SettingGetter.

        :arg settings: the config file settings
        :type settings: dict
        """
        self._settings = settings

    def get(self, envvar_name, default=None):
        """
        Return the value for the named setting.

        Return the value of the environment variable named ``envvar_name``.

        If no environment variable named ``envvar_name`` exists then return the
        correspondingly named config file setting.

        If neither the environment variable nor the config file setting exist
        then return ``default``.

        The config file setting name is ``envvar_name`` lower-cased. For
        example if ``envvar_name`` is ``FOO_BAR`` and there's no ``FOO_BAR``
        environment variable then a setting named ``foo_bar`` in the config
        file will be looked for.

        :arg envvar_name: the name of the environment variable to look for
        :type envvar_name: str
        :arg default: the default value for this setting

        :return: the setting's value
        """
        try:
            return os.environ[envvar_name]
        except KeyError:
            pass

        config_file_setting_name = envvar_name.lower()
        try:
            return self._settings[config_file_setting_name]
        except KeyError:
            pass

        return default
