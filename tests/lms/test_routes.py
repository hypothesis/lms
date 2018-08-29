# -*- coding: utf-8 -*-

import mock
from lms import routes


class TestIncludeMe:

    def test_it_adds_some_routes(self):
        config = mock.MagicMock()

        routes.includeme(config)

        expected_calls = [
        ]
        for call in expected_calls:
            assert call in config.mock_calls
