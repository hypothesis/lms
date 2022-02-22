from unittest.mock import sentinel

import pytest

from lms.views.api.refresh import RefreshViews


class TestRefreshViews:
    def test_get_refreshed_token_from_canvas(
        self, canvas_api_client, oauth2_token_service, views
    ):
        views.get_refreshed_token_from_canvas()

        canvas_api_client.get_refreshed_token.assert_called_once_with(
            oauth2_token_service.get.return_value.refresh_token
        )

    def test_get_refreshed_token_from_blackboard(self, blackboard_api_client, views):
        views.get_refreshed_token_from_blackboard()

        blackboard_api_client.refresh_access_token.assert_called_once_with()

    @pytest.fixture
    def views(self, pyramid_request):
        return RefreshViews(sentinel.context, pyramid_request)
