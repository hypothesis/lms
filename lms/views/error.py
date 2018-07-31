# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid import i18n
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid.settings import asbool

from lms.exceptions import MissingLTILaunchParamError

_ = i18n.TranslationStringFactory(__package__)


@view_defaults(renderer='lms:templates/error.html.jinja2')
class ErrorViews(object):
    """Show user an error page and an appropriate message."""

    def __init__(self, exc, request):
        """Store request and exception information."""
        self.exc = exc
        self.request = request

    @view_config(context=httpexceptions.HTTPError)
    @view_config(context=httpexceptions.HTTPServerError)
    def httperror(self):
        self.request.response.status_int = self.exc.status_int
        # If code raises an HTTPError or HTTPServerError we assume this was
        # deliberately raised and:
        # 1. Show the user an error page including specific error message
        # 2. _Do not_ report the error to Sentry
        return {'message': str(self.exc)}

    @view_config(context=Exception)
    def error(self):
        # In debug mode re-raise exceptions so that they get printed in the
        # terminal.
        if asbool(self.request.registry.settings.get('debug')):
            raise self.exc

        self.request.response.status_int = 500

        # If code raises a non-HTTPException exception we assume it was a bug
        # and:
        # 1. Show the user a generic error page
        # 2. Report the details of the error to Sentry
        self.request.raven.captureException()
        return {'message': _("Sorry, but something went wrong. "
                             "The issue has been reported and we'll try to "
                             "fix it.")}


    @view_config(context=MissingLTILaunchParamError)
    def missing_lti_launch_param_error(self):
        """
        Catch MissingLTILaunchParamError, render a 400 page and report the exception to Sentry.

        If code raises a MissingLTILaunchParamError it means that a required parameter was
        missing from an LTI launch request that we received:
        1. Show the user an error page including specific error message
        2. Report the error to Sentry
        """
        self.request.response.status_int = 400
        self.request.raven.captureException()
        return {'message': str(self.exc)}
