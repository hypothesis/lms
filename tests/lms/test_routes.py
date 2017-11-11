# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lms import routes

import mock


class TestIncludeMe(object):

    def test_it_adds_some_routes(self):
        config = mock.MagicMock()

        routes.includeme(config)

        expected_calls = [
        ]
        for call in expected_calls:
            assert call in config.mock_calls
