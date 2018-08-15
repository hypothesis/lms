# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pyramid import httpexceptions
import pytest

from lms.views import error
from lms.exceptions import MissingLTILaunchParamError, MissingLTIContentItemParamError


class TestErrorViews:
    def test_it_sets_correct_message_for_http_error(self, pyramid_request):
        exc = httpexceptions.HTTPError('test http error msg', status_code=500)

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.httperror()

        assert resp['message'] == 'test http error msg'

    def test_it_sets_correct_request_status_int_for_http_error(self, pyramid_request):
        exc = httpexceptions.HTTPError('test http error msg', status_code=500)

        error_views = error.ErrorViews(exc, pyramid_request)
        error_views.httperror()

        assert pyramid_request.response.status_int == exc.status_int

    def test_it_sets_correct_message_for_http_server_error(self, pyramid_request):
        exc = httpexceptions.HTTPServerError('test server error msg', status_code=500)

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.httperror()

        assert resp['message'] == 'test server error msg'

    def test_it_sets_correct_request_status_int_for_http_server_error(self, pyramid_request):
        exc = httpexceptions.HTTPServerError('test server error msg', status_code=500)

        error_views = error.ErrorViews(exc, pyramid_request)
        error_views.httperror()

        assert pyramid_request.response.status_int == exc.status_int

    def test_it_sets_correct_message_for_non_http_error(self, pyramid_request):
        exc = Exception()

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.error()

        assert resp['message'] == 'Sorry, but something went wrong. The issue has been reported and we\'ll try to fix it.'

    def test_it_sets_correct_status_int_for_non_http_error(self, pyramid_request):
        exc = Exception()

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.error()

        assert pyramid_request.response.status_int == 500

    def test_it_logs_non_http_error_in_sentry(self, pyramid_request):
        exc = Exception()

        error_views = error.ErrorViews(exc, pyramid_request)
        error_views.error()

        assert pyramid_request.raven.captureException.call_count == 1

    def test_it_re_raises_exception_in_debug_mode(self, pyramid_request):
        exc = Exception('test exception msg')
        pyramid_request.registry.settings = {'debug': True}

        error_views = error.ErrorViews(exc, pyramid_request)

        with pytest.raises(Exception, match="test exception msg"):
            error_views.error()

    def test_it_sets_correct_message_for_missing_lti_param_error_for_missing_lti_launch_params(self, pyramid_request):
        exc = MissingLTILaunchParamError('test lti launch param error msg')

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.missing_lti_param_error()

        assert resp['message'] == 'test lti launch param error msg'

    def test_it_sets_correct_status_int_for_missing_lti_param_error_for_missing_lti_launch_params(self, pyramid_request):
        exc = MissingLTILaunchParamError('test lti launch param error msg')

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.missing_lti_param_error()

        assert pyramid_request.response.status_int == 400

    def test_it_sets_correct_message_for_missing_lti_param_error_for_missing_lti_content_item_params(self, pyramid_request):
        exc = MissingLTIContentItemParamError('test lti launch param error msg')

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.missing_lti_param_error()

        assert resp['message'] == 'test lti launch param error msg'

    def test_it_sets_correct_status_int_for_missing_lti_param_error_for_missing_lti_content_item_params(self, pyramid_request):
        exc = MissingLTIContentItemParamError('test lti launch param error msg')

        error_views = error.ErrorViews(exc, pyramid_request)
        resp = error_views.missing_lti_param_error()

        assert pyramid_request.response.status_int == 400
