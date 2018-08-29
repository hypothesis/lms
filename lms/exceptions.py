# -*- coding: utf-8 -*-

"""Exceptions raised by LTI launch code."""

from pyramid.httpexceptions import HTTPBadRequest


class LTILaunchError(HTTPBadRequest):  # pylint: disable=too-many-ancestors
    """Base exception for problems handling LTI launches."""

    pass


class MissingLTILaunchParamError(LTILaunchError):  # pylint: disable=too-many-ancestors
    """Exception raised if params required for LTI launch are missing."""

    pass


class MissingLTIContentItemParamError(LTILaunchError):  # pylint: disable=too-many-ancestors
    """Exception raised if params required for LTI content item selection are missing."""

    pass
