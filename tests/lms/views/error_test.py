# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
import pytest

from lms.views import error
from lms.exceptions import MissingLtiLaunchParamError


class TestErrorController(object):
    def test_it_sets_correct_message_for_http_error(self, pyramid_request):
        exc = httpexceptions.HTTPError('test http error msg', status_code=500)

        error_controller = error.ErrorController(exc, pyramid_request)
        resp = error_controller.httperror()

        assert resp['message'] == 'test http error msg'

    def test_it_sets_correct_request_status_int_for_http_error(self, pyramid_request):
        exc = httpexceptions.HTTPError('test http error msg', status_code=500)

        error_controller = error.ErrorController(exc, pyramid_request)
        error_controller.httperror()

        assert pyramid_request.response.status_int == exc.status_int

    def test_it_sets_correct_message_for_http_server_error(self, pyramid_request):
        exc = httpexceptions.HTTPServerError('test server error msg', status_code=500)

        error_controller = error.ErrorController(exc, pyramid_request)
        resp = error_controller.httperror()

        assert resp['message'] == 'test server error msg'

    def test_it_sets_correct_request_status_int_for_http_server_error(self, pyramid_request):
        exc = httpexceptions.HTTPServerError('test server error msg', status_code=500)

        error_controller = error.ErrorController(exc, pyramid_request)
        error_controller.httperror()

        assert pyramid_request.response.status_int == exc.status_int

    def test_it_sets_correct_message_for_non_http_error(self, pyramid_request):
        exc = Exception()

        error_controller = error.ErrorController(exc, pyramid_request)
        resp = error_controller.error()

        assert resp['message'] == 'Sorry, but something went wrong. The issue has been reported and we\'ll try to fix it.'

    def test_it_sets_correct_status_int_for_non_http_error(self, pyramid_request):
        exc = Exception()

        error_controller = error.ErrorController(exc, pyramid_request)
        resp = error_controller.error()

        assert pyramid_request.response.status_int == 500

    def test_it_logs_non_http_error_in_sentry(self, pyramid_request):
        exc = Exception()

        error_controller = error.ErrorController(exc, pyramid_request)
        error_controller.error()

        pyramid_request.raven.captureException.assert_called_once()

    def test_it_re_raises_exception_in_debug_mode(self, pyramid_request):
        exc = Exception()
        pyramid_request.registry.settings = {'debug': True}

        error_controller = error.ErrorController(exc, pyramid_request)

        with pytest.raises(Exception):
            error_controller.error()

    def test_it_logs_missing_lti_launch_param_error_in_sentry(self, pyramid_request):
        exc = MissingLtiLaunchParamError('test lti launch param error msg')

        error_controller = error.ErrorController(exc, pyramid_request)
        error_controller.ltilauncherror()

        pyramid_request.raven.captureException.assert_called_once()

    def test_it_sets_correct_message_for_missing_lti_param_error(self, pyramid_request):
        exc = MissingLtiLaunchParamError('test lti launch param error msg')

        error_controller = error.ErrorController(exc, pyramid_request)
        resp = error_controller.ltilauncherror()

        assert resp['message'] == 'test lti launch param error msg'

    def test_it_sets_correct_status_int_for_missing_lti_param_error(self, pyramid_request):
        exc = MissingLtiLaunchParamError('test lti launch param error msg')

        error_controller = error.ErrorController(exc, pyramid_request)
        resp = error_controller.ltilauncherror()

        assert pyramid_request.response.status_int == 400
