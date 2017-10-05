# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import md5

from lti.views import web

import pytest
import mock


@pytest.mark.usefixtures('requests', 'render', 'util', 'Response')
class TestWebResponse(object):

    def test_it_gets_the_canvas_servers_url_from_the_database(self,
                                                              pyramid_request,
                                                              open_,
                                                              auth_data_svc):
        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        auth_data_svc.get_canvas_server.assert_called_once_with('TEST_OAUTH_CONSUMER_KEY')

    def test_it_checks_whether_the_file_is_already_cached(self,
                                                          pyramid_request,
                                                          open_,
                                                          util,
                                                          auth_data_svc):
        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        util.filecache.exists_html.assert_called_once_with(
            self.expected_hash(), pyramid_request.registry.settings)

    def test_if_its_not_already_cached_it_gets_it_from_via(self,  # pylint:disable=too-many-arguments
                                                           pyramid_request,
                                                           util,
                                                           requests,
                                                           open_,
                                                           auth_data_svc):
        util.filecache.exists_html.return_value = False

        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        requests.get.assert_called_once_with(
            'https://via.hypothes.is/TEST_ASSIGNMENT_VALUE',
            headers={'User-Agent': 'Mozilla'},
        )

    def test_if_its_not_already_cached_it_caches_it(self,  # pylint:disable=too-many-arguments
                                                    pyramid_request,
                                                    util,
                                                    open_,
                                                    auth_data_svc):
        util.filecache.exists_html.return_value = False

        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        open_.assert_called_once_with('/var/lib/lti/' + self.expected_hash() + '.html', 'wb')
        open_.return_value.write.assert_called_once_with("The text of the web page")
        open_.return_value.close.assert_called_once_with()

    # This is necessary to work around problems with running Via's responses
    # inside Canvas's iframe.
    def test_it_comments_out_returns_statements_in_vias_response(self,  # pylint:disable=too-many-arguments
                                                                 pyramid_request,
                                                                 util,
                                                                 requests,
                                                                 open_,
                                                                 auth_data_svc):
        util.filecache.exists_html.return_value = False
        requests.get.return_value.text = (
            "return; should be commented out")

        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        open_.return_value.write.assert_called_once_with(
            "// return should be commented out")

    def test_it_changes_src_attributes_in_vias_response(self,  # pylint:disable=too-many-arguments
                                                        pyramid_request,
                                                        util,
                                                        requests,
                                                        open_,
                                                        auth_data_svc):
        util.filecache.exists_html.return_value = False
        requests.get.return_value.text = ('src="/im_something"')

        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        open_.return_value.write.assert_called_once_with('src="https://via.hypothes.issomething"')

    def test_if_the_page_is_already_cached_it_doesnt_request_it_from_via(  # pylint:disable=too-many-arguments
            self, pyramid_request, util, requests, open_, auth_data_svc):
        util.filecache.exists_html.return_value = True

        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        assert not requests.get.called

    def test_if_the_page_is_already_cached_it_doesnt_write_to_the_filesystem(  # pylint:disable=too-many-arguments
            self, pyramid_request, util, open_, auth_data_svc):
        util.filecache.exists_html.return_value = True

        web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        assert not open_.called

    @pytest.mark.parametrize('already_cached', [True, False])
    def test_it_returns_the_modified_Via_page(self,  # pylint:disable=too-many-arguments
                                              pyramid_request,
                                              open_,
                                              render,
                                              Response,
                                              already_cached,
                                              util,
                                              auth_data_svc):
        # It returns the modified Via page as an HTML response,
        # regardless of whether the page was retrieved from the cache or has
        # just been fetched from Via now.
        util.filecache.exists_html.return_value = already_cached

        render.return_value = 'THE_RENDERED_HTML_PAGE'

        response = web.web_response(
            request=pyramid_request,
            auth_data_svc=auth_data_svc,
            oauth_consumer_key='TEST_OAUTH_CONSUMER_KEY',
            course='TEST_COURSE_ID',
            lis_outcome_service_url='TEST_LIS_OUTCOME_SERVICE_URL',
            lis_result_sourcedid='TEST_LIS_RESULT_SOURCEDID',
            name='TEST_ASSIGNMENT_NAME',
            value='TEST_ASSIGNMENT_VALUE',
            open_=open_,
        )

        render.assert_called_once_with('lti:templates/html_assignment.html.jinja2', {
            'name': 'TEST_ASSIGNMENT_NAME',
            'path': '/cache/' + self.expected_hash() + '.html',
            'oauth_consumer_key': 'TEST_OAUTH_CONSUMER_KEY',
            'lis_outcome_service_url': 'TEST_LIS_OUTCOME_SERVICE_URL',
            'lis_result_sourcedid': 'TEST_LIS_RESULT_SOURCEDID',
            'lti_server': 'http://TEST_LTI_SERVER.com',
        })
        Response.assert_called_once_with('THE_RENDERED_HTML_PAGE',
                                         content_type='text/html')
        assert response == Response.return_value

    def expected_hash(self):
        """Return the hash for the test web page we're annotating."""
        md5_obj = md5.new()
        md5_obj.update('https://TEST_CANVAS_SERVER.com/TEST_COURSE_ID/TEST_ASSIGNMENT_VALUE')
        return md5_obj.hexdigest()

    @pytest.fixture
    def requests(self, patch):
        requests = patch('lti.views.web.requests')

        # The responses that web_response() gets when it calls Via.
        requests.get.return_value.status_code = 200
        requests.get.return_value.text = "The text of the web page"

        return requests

    @pytest.fixture
    def open_(self):
        return mock.MagicMock()

    @pytest.fixture
    def render(self, patch):
        return patch('lti.views.web.render')

    @pytest.fixture
    def util(self, patch):
        return patch('lti.views.web.util')

    @pytest.fixture
    def Response(self, patch):
        return patch('lti.views.web.Response')
