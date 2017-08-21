# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import md5

import pytest
import mock

from lti.views import pdf


@pytest.mark.usefixtures('requests',
                         'util',
                         'render',
                         'oauth',
                         'urlretrieve',
                         'shutil',
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

    def test_it_checks_whether_the_pdf_file_is_already_cached(self,
                                                              pyramid_request,
                                                              util):
        pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL', 
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        util.filecache.exists_pdf.assert_called_once_with(
            self.expected_digest(), pyramid_request.registry.settings)

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

    def test_if_the_canvas_api_200s_it_downloads_the_PDF_file(self,
                                                              pyramid_request,
                                                              requests,
                                                              urlretrieve,
                                                              util):
        util.filecache.exists_pdf.return_value = False
        requests.Session.return_value.get.return_value.status_code = 200
        requests.Session.return_value.get.return_value.json.return_value = {
            'url': 'THE_URL_OF_THE_PDF_FILE',
        }

        response = pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL', 
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        urlretrieve.assert_called_once_with(
            'THE_URL_OF_THE_PDF_FILE',
            self.expected_digest(),
        )

    def test_it_moves_the_downloaded_file_into_the_FILES_PATH_folder(self,
                                                                     pyramid_request,
                                                                     util,
                                                                     requests,
                                                                     shutil):
        util.filecache.exists_pdf.return_value = False
        requests.Session.return_value.get.return_value.status_code = 200

        pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL', 
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        expected_digest = self.expected_digest()
        shutil.move.assert_called_once_with(
            expected_digest, '/var/lib/lti/' + expected_digest + '.pdf')

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

        expected_digest = self.expected_digest()
        render.assert_called_once_with(
            'lti:templates/pdf_assignment.html.jinja2', dict(
                name='TEST_NAME',
                hash=expected_digest,
                oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
                lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL', 
                lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
                doc_uri='http://TEST_LTI_SERVER.com/viewer/web/' + expected_digest + '.pdf',
                lti_server='http://TEST_LTI_SERVER.com',
        ))
        Response.assert_called_once_with(
            render.return_value.encode.return_value, content_type='text/html')
        assert response == Response.return_value

    def test_if_get_fingerprint_returns_a_value_it_uses_that_as_pdf_uri_instead(
            self, pyramid_request, util, render):
        util.pdf.get_fingerprint.return_value = 'abc123'

        pdf.lti_pdf(
            pyramid_request,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL', 
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            course='TEST_COURSE',
            name='TEST_NAME',
            value='TEST_VALUE',
        )

        assert render.call_args[0][1]['doc_uri'] == 'urn:x-pdf:abc123'

    def expected_digest(self):
        """Return the MD5 digest we expect lti_pdf() to cache the file with."""
        md5_obj = md5.new()
        md5_obj.update('https://TEST_CANVAS_SERVER.com/TEST_COURSE/TEST_VALUE')
        return md5_obj.hexdigest()

    @pytest.fixture
    def requests(self, patch):
        return patch('lti.views.pdf.requests')

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
    def shutil(self, patch):
        return patch('lti.views.pdf.shutil')

    @pytest.fixture
    def Response(self, patch):
        return patch('lti.views.pdf.Response')
