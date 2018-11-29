# -*- coding: utf-8 -*-

"""Exceptions raised by lms.util code."""


class UtilError(Exception):
    pass


class MissingToolConsumerIntanceGUIDError(UtilError):
    pass


class MissingUserIDError(UtilError):
    pass
