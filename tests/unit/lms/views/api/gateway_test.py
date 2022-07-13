from unittest.mock import sentinel

import pytest

from lms.views.api.gateway import h_lti


@pytest.mark.usefixtures("grant_token_service")
class TestHLTI:
    def test_it_adds_h_api_details(self, pyramid_request, grant_token_service):
        response = h_lti(pyramid_request)

        grant_token_service.generate_token.assert_called_once_with(
            pyramid_request.lti_user.h_user
        )
        h_api_url = pyramid_request.registry.settings["h_api_url_public"]
        assert response["h_api"] == {
            "list_endpoints": {
                "method": "GET",
                "url": h_api_url,
                "headers": {"Accept": "application/vnd.hypothesis.v2+json"},
            },
            "exchange_grant_token": {
                "method": "POST",
                "url": h_api_url + "token",
                "headers": {
                    "Accept": "application/vnd.hypothesis.v2+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "data": {
                    "assertion": grant_token_service.generate_token.return_value,
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                },
            },
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params["tool_consumer_instance_guid"] = sentinel.guid

        return pyramid_request
