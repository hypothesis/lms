from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.config import Configurator

from lms.models.lti_params import CLAIM_PREFIX, LTIParams, _get_lti_params, includeme


class TestLTI13Params:
    @pytest.mark.parametrize(
        "lti_11_key,value",
        [
            ("user_id", "USER_ID"),
            ("roles", "Instructor,Student"),
            ("tool_consumer_instance_guid", "GUID"),
            ("tool_consumer_info_product_family_code", "FAMILY_CODE"),
            ("lis_person_name_given", "GIVEN_NAME"),
            ("lis_person_name_family", "FAMILY_NAME"),
            ("lis_person_name_full", "FULL_NAME"),
            ("context_id", "CONTEXT_ID"),
            ("context_title", "CONTEXT_TITLE"),
            ("lti_version", "LTI_VERSION"),
            ("lti_message_type", "LTI_MESSAGE_TYPE"),
            ("resource_link_id", "RESOURCE_LINK_ID"),
        ],
    )
    def test_v13_mappings(self, lti_v13_params, lti_11_key, value):
        assert LTIParams.from_v13(lti_v13_params)[lti_11_key] == value

    def test_v13_non_existing(self):
        assert not LTIParams.from_v13({}).v11

    def test_v11(self):
        sample_dict = {"test": "key"}

        params = LTIParams(sample_dict)
        assert params == params.v11 == sample_dict

    def test_it_doesnt_set_partial_keys(self):
        params = LTIParams.from_v13(
            {
                "https://purl.imsglobal.org/spec/lti/claim/custom": {
                    "canvas_course_id": "SOME_ID"
                }
            }
        )

        # The existent params get returned
        assert params["custom_canvas_course_id"] == "SOME_ID"
        # Nonexistent ones in the same "level" are not present
        assert "custom_canvas_api_domain" not in params

    def test_prefers_lti1p1_ids(self):
        params = LTIParams.from_v13(
            {
                "sub": "v13",
                f"{CLAIM_PREFIX}/resource_link_id": {"id": "v13"},
                f"{CLAIM_PREFIX}/lti1p1": {
                    "user_id": "user_id-v11",
                    "resource_link_id": "resource_link_id-v11",
                },
            }
        )

        assert params["user_id"] == "user_id-v11"
        assert params["resource_link_id"] == "resource_link_id-v11"

    @pytest.mark.parametrize(
        "parameter_name,claim_name",
        [
            ("custom_canvas_course_id", "canvas_course_id"),
            ("custom_canvas_user_id", "canvas_user_id"),
        ],
    )
    def test_integer_canvas_parameters(self, parameter_name, claim_name):
        params = LTIParams.from_v13({f"{CLAIM_PREFIX}/custom": {claim_name: 1}})

        assert isinstance(params[parameter_name], str)
        assert params[parameter_name] == "1"


class TestGetLTIParams:
    def test_with_lti_jwt(self, LTIParams, pyramid_request):
        pyramid_request.lti_jwt = sentinel.lti_jwt

        lti_params = _get_lti_params(pyramid_request)

        LTIParams.from_v13.assert_called_once_with(sentinel.lti_jwt)
        assert lti_params == LTIParams.from_v13.return_value

    def test_without_lti_jwt(self, pyramid_request):
        pyramid_request.lti_jwt = None
        pyramid_request.params = sentinel.params

        assert _get_lti_params(pyramid_request) == sentinel.params

    @pytest.fixture
    def LTIParams(self, patch):
        return patch("lms.models.lti_params.LTIParams")


class TestIncludeMe:
    def test_it_sets_lti_jwt(self, configurator):
        includeme(configurator)

        configurator.add_request_method.assert_called_once_with(
            _get_lti_params, name="lti_params", property=True, reify=True
        )

    @pytest.fixture()
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)
