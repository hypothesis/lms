# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti.views import web

import pytest


@pytest.mark.usefixtures('render', 'Response')
class TestWebResponse(object):

    def test_it_returns_the_expected_response(self,  # pylint:disable=too-many-arguments
                                              pyramid_request,
                                              render,
                                              Response):
        render.return_value = 'THE_RENDERED_HTML_PAGE'

        response = web.web_response(
            request=pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            url='TEST_ASSIGNMENT_URL',
        )

        render.assert_called_once_with('lti:templates/html_assignment.html.jinja2', {
            'name': 'TEST_ASSIGNMENT_NAME',
            'url': 'http://TEST_VIA_SERVER.is/TEST_ASSIGNMENT_URL',
            'oauth_consumer_key': 'TEST_OAUTH_CONSUMER_KEY',
            'lis_outcome_service_url': 'TEST_LIS_OUTCOME_SERVICE_URL',
            'lis_result_sourcedid': 'TEST_LIS_RESULT_SOURCEDID',
            'lti_server': 'http://TEST_LTI_SERVER.com',
        })
        Response.assert_called_once_with('THE_RENDERED_HTML_PAGE',
                                         content_type='text/html')
        assert response == Response.return_value

    @pytest.fixture
    def render(self, patch):
        return patch('lti.views.web.render')

    @pytest.fixture
    def Response(self, patch):
        return patch('lti.views.web.Response')
