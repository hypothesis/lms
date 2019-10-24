from unittest import mock

import pytest

from lms.services import HAPIError
from lms.services.h_api_client import HAPIClient
from lms.services.h_api_requests import HAPIRequests
from lms.values import HUser


class TestHAPIClient:
    def test_get_user_fetches_user(self, h_api, h_api_client, user_response):
        h_api.get().json.return_value = user_response

        user = h_api_client.get_user("user123")

        h_api.get.assert_called_with(path="users/acct:user123@TEST_AUTHORITY")
        assert user == HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

    def test_get_user_raises_if_call_fails(self, h_api, h_api_client):
        h_api.get.side_effect = HAPIError("Unknown user")

        with pytest.raises(HAPIError):
            h_api_client.get_user("unknown_user")

    @pytest.fixture
    def user_response(self):
        return {"display_name": "Jim Smith"}

    @pytest.fixture
    def h_api_client(self, h_api, pyramid_request):
        return HAPIClient({}, pyramid_request)

    @pytest.fixture
    def h_api(self, pyramid_config):
        svc = mock.create_autospec(HAPIRequests, instance=True)
        pyramid_config.register_service(svc, name="h_api_requests")
        return svc
