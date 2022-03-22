import pytest

from lms.models import LTIParams


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
