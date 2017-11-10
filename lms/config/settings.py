# -*- coding: utf-8 -*-

"""Functions for reading config settings."""

from __future__ import unicode_literals

import os


class SettingError(Exception):
    pass


def env_setting(envvar_name, required=False, default=None):
    try:
        return os.environ[envvar_name]
    except KeyError:
        if default is not None:
            return default
        if required is True:
            raise SettingError(
                "environment variable {envvar_name} isn't set".format(
                    envvar_name=envvar_name,
                )
            )
