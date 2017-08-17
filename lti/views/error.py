# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
from pyramid import i18n
from pyramid.view import view_config
from pyramid.view import view_defaults
from pyramid.settings import asbool


_ = i18n.TranslationStringFactory(__package__)


@view_defaults(renderer='lti:templates/error.html.jinja2')
class ErrorController(object):

    def __init__(self, exc, request):
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
