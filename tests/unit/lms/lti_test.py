import pytest
from pytest import param

from lms.lti import LTI13Params, _ParamMapping


def sample_function(value):
    return value * 2


class TestLTI13Params:
    @pytest.mark.parametrize(
        "key,mapping,data,expected",
        [
            param("key", None, {"key": "value"}, "value", id="no mapping"),
            param(
                "key",
                _ParamMapping("key"),
                {"key": "value"},
                "value",
                id="single key mapping",
            ),
            param(
                "key",
                _ParamMapping("key", "sub"),
                {"key": {"sub": "sub value"}},
                "sub value",
                id="nested key mapping",
            ),
            param(
                "key",
                _ParamMapping("key", function=sample_function),
                {"key": "value"},
                "valuevalue",
                id="with function",
            ),
        ],
    )
    def test_it(self, key, mapping, data, expected):
        lti_params = LTI13Params(data)
        if mapping:
            lti_params.lti_param_mapping[key] = mapping

        assert lti_params[key] == expected

        if mapping:
            del lti_params.lti_param_mapping[key]

    @pytest.mark.parametrize(
        "key,data,default,expected",
        [
            param("key", {"key": "value"}, "default", "value", id="existing"),
            param("key", {"notkey": "value"}, "default", "default", id="default"),
        ],
    )
    def test_get(self, key, data, default, expected):
        assert LTI13Params(data).get(key, default) == expected

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
            ("issuer", "ISSUER"),
            ("client_id", "CLIENT_ID"),
            ("deployment_id", "DEPLOYMENT_ID"),
        ],
    )
    def test_13_mappings(self, lti_13_launch_params, lti_11_key, value):
        assert LTI13Params(lti_13_launch_params)[lti_11_key] == value

    @pytest.fixture
    def lti_13_launch_params(self):
        return {
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LTI_MESSAGE_TYPE",
            "https://purl.imsglobal.org/spec/lti/claim/version": "LTI_VERSION",
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
                "id": "RESOURCE_LINK_ID",
                "description": "",
                "title": "Test assignment",
                "validation_context": None,
                "errors": {"errors": {}},
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
                "type": [
                    "http://purl.imsglobal.org/vocab/lis/v2/course#CourseOffering"
                ],
                "validation_context": None,
                "errors": {"errors": {}},
            },
            "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
                "guid": "GUID",
                "name": "University of Hypothesis",
                "version": "cloud",
                "product_family_code": "FAMILY_CODE",
                "validation_context": None,
                "errors": {"errors": {}},
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
