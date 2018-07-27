# -*- coding: utf-8 -*-

"""Functions for reading config settings."""

from __future__ import unicode_literals

import os


class SettingError(Exception):
    pass


def env_setting(envvar_name, required=False, default=None, callback=None):
    try:
        value = os.environ[envvar_name]
    except KeyError:
        if default is not None:
            value = default
        elif required is True:
            raise SettingError(
                "environment variable {envvar_name} isn't set".format(
                    envvar_name=envvar_name,
                )
            )
        else:
            value = None

    if callback:
        value = callback(value)

    return value
