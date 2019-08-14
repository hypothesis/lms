from unittest import mock

import pytest

from lms.services import HAPIError
from lms.services.hapi import HypothesisAPIService
from lms.services.h_operations import HypothesisOperationsService
from lms.values import HUser


class TestHypothesisOperationsService:
    def test_fetch_user_fetches_user(self, hapi_service, hops_service, user_response):
        hapi_service.get().json.return_value = user_response

        user = hops_service.fetch_user("user123")

        hapi_service.get.assert_called_with(path="users/acct:user123@TEST_AUTHORITY")
        assert user == HUser(
            authority="TEST_AUTHORITY", username="user123", display_name="Jim Smith"
        )

    def test_fetch_user_raises_if_call_fails(self, hapi_service, hops_service):
        hapi_service.get.side_effect = HAPIError("Unknown user")

        with pytest.raises(HAPIError):
            hops_service.fetch_user("unknown_user")

    @pytest.fixture
    def user_response(self):
        return {"display_name": "Jim Smith"}

    @pytest.fixture
    def hops_service(self, hapi_service, pyramid_request):
        return HypothesisOperationsService({}, pyramid_request)

    @pytest.fixture
    def hapi_service(self, pyramid_config):
        svc = mock.create_autospec(HypothesisAPIService, instance=True)
        pyramid_config.register_service(svc, name="hapi")
        return svc
