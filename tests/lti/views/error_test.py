# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from pyramid import httpexceptions

from lti.views.error import ErrorController


class TestErrorController(object):

    def test_httperror_sets_status_code(self, pyramid_request):
        ErrorController(httpexceptions.HTTPNotFound(), pyramid_request).httperror()

        assert pyramid_request.response.status_int == 404

    def test_httperror_returns_error_message(self, pyramid_request):
        exc = httpexceptions.HTTPNotFound("Annotation not found")
        controller = ErrorController(exc, pyramid_request)

        template_data = controller.httperror()

        assert template_data["message"] == "Annotation not found"

    def test_error_sets_status_code(self, pyramid_request):
        ErrorController(Exception(), pyramid_request).error()

        assert pyramid_request.response.status_int == 500

    def test_error_raises_in_debug_mode(self, pyramid_request):
        pyramid_request.registry.settings["debug"] = True

        with pytest.raises(Exception):
            ErrorController(Exception(), pyramid_request).error()

    def test_error_reports_to_sentry(self, pyramid_request):
        ErrorController(Exception(), pyramid_request).error()

        pyramid_request.raven.captureException.assert_called_once_with()

    def test_error_returns_error_message(self, pyramid_request):
        controller = ErrorController(Exception(), pyramid_request)

        template_data = controller.error()

        assert template_data["message"].startswith("Sorry, but")
