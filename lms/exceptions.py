# -*- coding: utf-8 -*-

"""Exceptions raised by lti launch code."""

from __future__ import unicode_literals

from pyramid.i18n import TranslationString as _  # noqa: N813


class LtiLaunchError(Exception):
    """Base exception for problems handling LTI launches."""

    def __init__(self, message, status_int=400):
        """Store exception message and status code."""
        self.status_int = status_int
        super(LtiLaunchError, self).__init__(message)


class MissingLtiLaunchParamError(LtiLaunchError):
    """Exception raised if params required for lti launch are missing."""

    def __init__(self, msg):
        """Initialise with a message and status code."""
        super(MissingLtiLaunchParamError, self).__init__(_(msg), status_int=400)
