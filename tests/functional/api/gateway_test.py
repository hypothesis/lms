from functools import partial

import pytest
from h_matchers import Any

# pylint: disable=wildcard-import,unused-wildcard-import
from tests.conftest import TEST_SETTINGS
from tests.functional.oauth1 import *


class TestGatewayHLTI:
    def test_minimum_viable_login(self, gateway_launch, required_params):
        response = gateway_launch(required_params)

        assert response.headers["Content-Type"] == "application/json"
        assert response.json == {
            "api": {
                "h": {
                    "list_endpoints": {
                        "headers": {"Accept": "application/vnd.hypothesis.v2+json"},
                        "method": "GET",
                        "url": TEST_SETTINGS["h_api_url_public"],
                    },
                    "exchange_grant_token": {
                        "data": {
                            "assertion": Any.string(),
                            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                        },
                        "headers": {
                            "Accept": "application/vnd.hypothesis.v2+json",
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        "method": "POST",
                        "url": TEST_SETTINGS["h_api_url_public"] + "token",
                    },
                }
            }
        }

    @pytest.mark.parametrize(
        "param,status",
        (
            # Required for auth
            ("tool_consumer_instance_guid", 403),
            ("user_id", 403),
            ("roles", 403),
            # Required for us to work
            ("context_id", 422),
            # Us being picky, but useful for checking it's a well-formed
            # LTI launch
            ("lti_version", 422),
            ("lti_message_type", 422),
        ),
    )
    def test_each_param_is_required(
        self, gateway_launch, required_params, param, status
    ):
        required_params.pop(param)

        gateway_launch(required_params, status=status)

    def test_guid_must_match(self, gateway_launch, required_params):
        required_params["tool_consumer_instance_guid"] = "NOT MATCHING"

        gateway_launch(required_params, status=403)

    @pytest.mark.parametrize("auth_field", ("consumer_key", "shared_secret"))
    def test_signature_must_be_valid(
        self, gateway_launch, required_params, oauth1_credentials, auth_field
    ):
        oauth1_credentials[auth_field] = "WRONG"

        gateway_launch(required_params, status=403)

    @pytest.fixture
    def required_params(self, application_instance):
        return {
            "tool_consumer_instance_guid": application_instance.tool_consumer_instance_guid,
            "user_id": "123",
            "roles": "Instructor",
            "context_id": "321",
            "lti_version": "LTI-1p0",
            "lti_message_type": "basic-lti-launch-request",
        }

    @pytest.fixture
    def gateway_launch(self, do_lti_launch):
        return partial(
            do_lti_launch,
            "http://localhost/api/gateway/h/lti",
            headers={"Accept": "application/json"},
        )
