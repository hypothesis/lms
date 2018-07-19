# -*- coding: utf-8 -*-

"""Exceptions raised by lms.util code."""

from __future__ import unicode_literals


class UtilError(Exception):
    pass


class MissingToolConsumerIntanceGUIDError(UtilError):
    pass


class MissingUserIDError(UtilError):
    pass
