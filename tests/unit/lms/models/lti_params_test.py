import pytest

from lms.models import CLAIM_PREFIX, LTIParams


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
