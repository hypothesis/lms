# -*- coding: utf-8 -*-

"""Functions for reading config settings."""

from __future__ import unicode_literals

import os


class SettingError(Exception):
    pass


def env_setting(envvar_name):
    try:
        return os.environ[envvar_name]
    except KeyError:
        raise SettingError(
            "environment variable {envvar_name} isn't set".format(
                envvar_name=envvar_name)
        )


def optional_env_setting(envvar_name):
    try:
        return env_setting(envvar_name)
    except SettingError:
        return None
