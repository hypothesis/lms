# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti import routes

import mock


class TestIncludeMe(object):

    def test_it_adds_some_routes(self):
        config = mock.MagicMock()

        routes.includeme(config)

        expected_calls = [
            mock.call.add_route('about', '/'),
            mock.call.add_route('token_callback', '/token_callback'),
            mock.call.add_route('refresh_callback', '/refresh_callback'),
            mock.call.add_route('config_xml', '/config.xml'),
            mock.call.add_route('lti_credentials', '/lti_credentials'),
            mock.call.add_route('lti_setup', '/lti_setup'),
            mock.call.add_route('lti_submit', '/lti_submit'),
            mock.call.add_route('lti_export', '/lti_export'),
            mock.call.add_route('lti_serve_pdf', '/viewer/web/{file}.pdf'),
            mock.call.add_route('catchall_pdf', '/viewer/*subpath'),
        ]
        for call in expected_calls:
            assert call in config.mock_calls
