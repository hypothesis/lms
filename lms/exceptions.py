# -*- coding: utf-8 -*-

"""Exceptions raised by lti launch code."""

from __future__ import unicode_literals

from pyramid.httpexceptions import HTTPBadRequest


class LTILaunchError(HTTPBadRequest):  # pylint: disable=too-many-ancestors
    """Base exception for problems handling LTI launches."""

    pass


class MissingLTILaunchParamError(LTILaunchError):  # pylint: disable=too-many-ancestors
    """Exception raised if params required for lti launch are missing."""

    pass
