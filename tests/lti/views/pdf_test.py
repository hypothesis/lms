# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from lti.views import pdf


@pytest.mark.usefixtures('requests',
                         'util',
                         'render',
                         'oauth',
                         'urlretrieve',
                         'Response')
class TestLTIPDF(object):

    def test_it_gets_the_access_token_from_the_db(self,
                                                  pyramid_request,
                                                  auth_data_svc):
        pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        auth_data_svc.get_lti_token.assert_called_once_with('TEST_OAUTH_CONSUMER_KEY')

    def test_it_shows_an_error_page_if_we_dont_have_the_consumer_key(self,
                                                                     pyramid_request,
                                                                     util,
                                                                     auth_data_svc):
        auth_data_svc.get_lti_token.side_effect = KeyError

        response = pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        util.simple_response.assert_called_once_with(
            "We don't have the Consumer Key TEST_OAUTH_CONSUMER_KEY in our database yet.")
        assert response == util.simple_response.return_value

    def test_it_gets_the_canvas_servers_url_from_the_db(self,
                                                        pyramid_request,
                                                        auth_data_svc):
        pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        auth_data_svc.get_canvas_server.assert_called_once_with('TEST_OAUTH_CONSUMER_KEY')

    def test_if_the_file_isnt_cached_it_gets_the_file_metadata_from_canvas(self,
                                                                           pyramid_request,
                                                                           requests,
                                                                           util):
        util.filecache.exists_pdf.return_value = False

        pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        requests.Session.assert_called_once_with()
        requests.Session.return_value.get.assert_called_once_with(
            url='https://TEST_CANVAS_SERVER.com/api/v1/courses/TEST_COURSE/files/TEST_VALUE',
            headers={'Authorization': 'Bearer TEST_OAUTH_ACCESS_TOKEN'})

    # If the Canvas API returns a 401 Unauthorized when we try to access the
    # PDF file metadata then it kicks off an OAuth 2.0 authorization code flow.
    def test_if_the_canvas_api_401s_it_starts_an_oauth_flow(self,
                                                            pyramid_request,
                                                            requests,
                                                            oauth,
                                                            util):
        util.filecache.exists_pdf.return_value = False
        requests.Session.return_value.get.return_value.status_code = 401

        # In production capture_post_data() would return several parameters
        # that Canvas POSTed to us. For this test we'll just make it simple.
        util.requests.capture_post_data.return_value = {'foo': 'bar'}

        response = pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        # It captures certain of the parameters the Canvas POSTs to us.
        # Later it will pass them to oauth.make_authorization_request().
        util.requests.capture_post_data.assert_called_once_with(pyramid_request)

        oauth.make_authorization_request.assert_called_once_with(
            pyramid_request,
            # This is the dict that capture_post_data() returned, dumped to
            # JSON and URL-quoted, and with "pdf:" prepended.
            'pdf:%7B%22foo%22%3A%20%22bar%22%7D',
            refresh=True)

        assert response == oauth.make_authorization_request.return_value

    def test_it_renders_the_pdf_assignment_template(self,
                                                    pyramid_request,
                                                    render,
                                                    Response,
                                                    util):
        util.pdf.get_fingerprint.return_value = None

        response = pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        render.assert_called_once_with(
            'lti:templates/pdf_assignment.html.jinja2', dict(
                name='TEST_NAME',
                pdf_url='THE_DOWNLOAD_URL',
                oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
                lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
                lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
                lti_server='http://TEST_LTI_SERVER.com',
                client_origin='http://TEST_H_SERVER.is',
                via_url='http://TEST_VIA_SERVER.is',
            ),
        )
        Response.assert_called_once_with(
            render.return_value.encode.return_value, content_type='text/html')
        assert response == Response.return_value

    @pytest.fixture
    def requests(self, patch):
        requests = patch('lti.views.pdf.requests')
        requests.Session.return_value.get.return_value.status_code = 200
        requests.Session.return_value.get.return_value.json.return_value = {
            'url': 'THE_DOWNLOAD_URL',
        }
        return requests

    @pytest.fixture
    def util(self, patch):
        util = patch('lti.views.pdf.util')
        return util

    @pytest.fixture
    def render(self, patch):
        return patch('lti.views.pdf.render')

    @pytest.fixture
    def oauth(self, patch):
        return patch('lti.views.pdf.oauth')

    @pytest.fixture
    def urlretrieve(self, patch):
        return patch('lti.views.pdf.urllib.urlretrieve')

    @pytest.fixture
    def Response(self, patch):
        return patch('lti.views.pdf.Response')
