from unittest.mock import create_autospec

import pytest
from pyramid.config import Configurator

from lms.models.lti_params import CLAIM_PREFIX, LTIParams, includeme


class TestLTIParams:
    @pytest.mark.parametrize(
        "lti_11_key,value",
        [
            ("user_id", "USER_ID"),
            ("roles", "Instructor,Student"),
            ("tool_consumer_instance_guid", "GUID"),
            ("tool_consumer_info_product_family_code", "FAMILY_CODE"),
            ("tool_consumer_instance_contact_email", "CONTACT_EMAIL"),
            ("tool_consumer_instance_name", "PLATFORM_NAME"),
            ("tool_consumer_instance_description", "PLATFORM_DESCRIPTION"),
            ("tool_consumer_instance_url", "PLATFORM_URL"),
            ("tool_consumer_info_version", "PLATFORM_VERSION"),
            ("lis_person_name_given", "GIVEN_NAME"),
            ("lis_person_name_family", "FAMILY_NAME"),
            ("lis_person_name_full", "FULL_NAME"),
            ("lis_person_contact_email_primary", "EMAIL"),
            ("lis_person_sourcedid", "LIS_PERSON_SOURCEID"),
            ("context_id", "CONTEXT_ID"),
            ("context_title", "CONTEXT_TITLE"),
            ("lti_version", "LTI_VERSION"),
            ("lti_message_type", "LTI_MESSAGE_TYPE"),
            ("resource_link_id", "RESOURCE_LINK_ID"),
            ("resource_link_title", "RESOURCE_LINK_TITLE"),
            ("resource_link_description", "RESOURCE_LINK_DESCRIPTION"),
            ("org_defined_id", "ORG_DEFINED_ID"),
        ],
    )
    def test_v13_mappings(self, pyramid_request, lti_v13_params, lti_11_key, value):
        pyramid_request.lti_jwt = lti_v13_params

        assert LTIParams.from_request(pyramid_request)[lti_11_key] == value

    def test_v13_custom_fields(self, pyramid_request):
        pyramid_request.lti_jwt = {
            "https://purl.imsglobal.org/spec/lti/claim/custom": {"name": "value"}
        }

        assert LTIParams.from_request(pyramid_request)["custom_name"] == "value"

    def test_from_request_v11(self, pyramid_request):
        pyramid_request.params = {"test": "key"}

        params = LTIParams.from_request(pyramid_request)

        assert params == params.v11 == pyramid_request.params

    def test_from_request_json(self, pyramid_request):
        pyramid_request.json_body = {"test": "key"}
        pyramid_request.content_type = "application/json"

        params = LTIParams.from_request(pyramid_request)

        assert params == params.v11 == pyramid_request.json_body

    def test_v13_when_empty(self):
        lti_params = LTIParams({})

        assert not lti_params.v13.get("ANY KEY")

    def test_it_doesnt_set_partial_keys(self, pyramid_request):
        pyramid_request.lti_jwt = {
            "https://purl.imsglobal.org/spec/lti/claim/custom": {
                "canvas_course_id": "SOME_ID"
            }
        }

        params = LTIParams.from_request(pyramid_request)

        # The existent params get returned
        assert params["custom_canvas_course_id"] == "SOME_ID"
        # Nonexistent ones in the same "level" are not present
        assert "custom_canvas_api_domain" not in params

    def test_prefers_lti1p1_ids(self, pyramid_request):
        pyramid_request.lti_jwt = {
            "sub": "v13",
            f"{CLAIM_PREFIX}/resource_link_id": {"id": "v13"},
            f"{CLAIM_PREFIX}/lti1p1": {
                "user_id": "user_id-v11",
                "resource_link_id": "resource_link_id-v11",
            },
        }

        params = LTIParams.from_request(pyramid_request)

        assert params["user_id"] == "user_id-v11"
        assert params["resource_link_id"] == "resource_link_id-v11"

    def test_serialize(self):
        lti_params = LTIParams(
            {
                "oauth_nonce": "STRIPPED",
                "oauth_timestamp": "STRIPPED",
                "oauth_signature": "STRIPPED",
                "id_token": "STRIPPED",
                "other_values": "REMAIN",
            }
        )

        assert lti_params.serialize(extra="value") == {
            "other_values": "REMAIN",
            "extra": "value",
        }


class TestCanvasQuirks:
    @pytest.mark.parametrize(
        "speedgrader,expected",
        (("any_value", "canvas_value"), (None, "standard_value")),
    )
    def test_from_request_reads_resource_link_id(
        self, pyramid_request, speedgrader, expected
    ):
        pyramid_request.lti_jwt = {
            f"{CLAIM_PREFIX}/lti1p1": {"resource_link_id": "standard_value"}
        }
        pyramid_request.POST["resource_link_id"] = "DECOY"
        pyramid_request.GET["resource_link_id"] = "canvas_value"
        pyramid_request.GET["learner_canvas_user_id"] = speedgrader

        lti_params = LTIParams.from_request(pyramid_request)

        assert lti_params["resource_link_id"] == expected

    @pytest.mark.parametrize(
        "parameter_name,claim_name",
        [
            ("custom_canvas_course_id", "canvas_course_id"),
            ("custom_canvas_user_id", "canvas_user_id"),
        ],
    )
    def test_integer_canvas_parameters(
        self, pyramid_request, parameter_name, claim_name
    ):
        pyramid_request.lti_jwt = {f"{CLAIM_PREFIX}/custom": {claim_name: 1}}

        params = LTIParams.from_request(pyramid_request)

        assert isinstance(params[parameter_name], str)
        assert params[parameter_name] == "1"


class TestIncludeMe:
    def test_it_sets_lti_jwt(self, configurator):
        includeme(configurator)

        configurator.add_request_method.assert_called_once_with(
            LTIParams.from_request, name="lti_params", property=True, reify=True
        )

    @pytest.fixture()
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)
