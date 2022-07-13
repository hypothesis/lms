from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPForbidden

from lms.models import ReusedConsumerKey
from lms.resources import LTILaunchResource
from lms.views.api.gateway import h_lti


@pytest.mark.usefixtures("grant_token_service")
class TestHLTI:
    def test_it_adds_h_api_details(self, context, pyramid_request, grant_token_service):
        response = h_lti(context, pyramid_request)

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

    def test_it_checks_for_guid_agreement(self, context, pyramid_request):
        context.application_instance.check_guid_aligns.side_effect = ReusedConsumerKey(
            "old", "new"
        )

        with pytest.raises(HTTPForbidden):
            h_lti(context, pyramid_request)

    @pytest.fixture
    def context(self):
        return create_autospec(LTILaunchResource, instance=True, spec_set=True)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_params["tool_consumer_instance_guid"] = sentinel.guid

        return pyramid_request
