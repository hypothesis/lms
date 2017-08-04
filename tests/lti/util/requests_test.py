# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti import constants
from lti.util import requests


class TestCapturePostData(object):

    def test_it_returns_a_dict_containing_the_values_of_certain_request_params(
            self, pyramid_request):
        data = requests.capture_post_data(pyramid_request)

        assert data == {
            constants.OAUTH_CONSUMER_KEY: 'TEST_OAUTH_CONSUMER_KEY',
            constants.CUSTOM_CANVAS_USER_ID: 'TEST_CUSTOM_CANVAS_USER_ID',
            constants.CUSTOM_CANVAS_COURSE_ID: 'TEST_CUSTOM_CANVAS_COURSE_ID',
            constants.CUSTOM_CANVAS_ASSIGNMENT_ID: 'TEST_CUSTOM_CANVAS_ASSIGNMENT_ID',
            constants.EXT_CONTENT_RETURN_TYPES: 'TEST_EXT_CONTENT_RETURN_TYPES',
            constants.EXT_CONTENT_RETURN_URL: 'TEST_EXT_CONTENT_RETURN_URL',
            constants.LIS_OUTCOME_SERVICE_URL: 'TEST_LIS_OUTCOME_SERVICE_URL',
            constants.LIS_RESULT_SOURCEDID: 'TEST_LIS_RESULT_SOURCEDID',
        }

    def test_it_returns_None_for_any_missing_params(self, pyramid_request):
        del pyramid_request.POST[constants.CUSTOM_CANVAS_COURSE_ID]
        del pyramid_request.POST[constants.LIS_OUTCOME_SERVICE_URL]

        data = requests.capture_post_data(pyramid_request)

        assert data[constants.CUSTOM_CANVAS_COURSE_ID] is None
        assert data[constants.LIS_OUTCOME_SERVICE_URL] is None

    def test_it_ignores_other_request_params(self, pyramid_request):
        pyramid_request.POST['foo'] = 'bar'

        data = requests.capture_post_data(pyramid_request)

        assert 'foo' not in data
