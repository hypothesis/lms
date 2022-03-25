import pytest

from lms.lti import LTIParams


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
    def test_v13_mappings(self, lti_v13_launch_params, lti_11_key, value):
        assert LTIParams.from_v13(lti_v13_launch_params)[lti_11_key] == value

    def test_v13_non_existing(self):
        assert not LTIParams.from_v13({}).v11

    def test_v11(self):
        sample_dict = {"test": "key"}

        params = LTIParams(sample_dict)
        assert params == params.v11 == sample_dict

    @pytest.fixture
    def lti_v13_launch_params(self):
        return {
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LTI_MESSAGE_TYPE",
            "https://purl.imsglobal.org/spec/lti/claim/version": "LTI_VERSION",
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
                "id": "RESOURCE_LINK_ID",
            },
            "iss": "ISSUER",
            "aud": "CLIENT_ID",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "DEPLOYMENT_ID",
            "sub": "USER_ID",
            "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "http://localhost:8001/lti_launches?url=https%3A%2F%2Felpais.es",
            "email": "eng+canvasteacher@hypothes.is",
            "name": "FULL_NAME",
            "given_name": "GIVEN_NAME",
            "family_name": "FAMILY_NAME",
            "https://purl.imsglobal.org/spec/lti/claim/context": {
                "id": "CONTEXT_ID",
                "label": "LTI",
                "title": "CONTEXT_TITLE",
            },
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
                "guid": "GUID",
                "product_family_code": "FAMILY_CODE",
            },
            "https://purl.imsglobal.org/spec/lti/claim/roles": [
                "Instructor",
                "Student",
            ],
            "https://purl.imsglobal.org/spec/lti/claim/custom": {
                "canvas_course_id": 319,
                "canvas_api_domain": "hypothesis.instructure.com",
            },
        }
