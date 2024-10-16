import json
from unittest.mock import sentinel

import marshmallow
import pytest
from h_matchers import Any
from pyramid import testing

from lms.validation import (
    BasicLTILaunchSchema,
    ConfigureAssignmentSchema,
    DeepLinkingLTILaunchSchema,
    LTIToolRedirect,
    LTIV11CoreSchema,
    ValidationError,
)


class TestLTIV11CoreSchema:
    def test_with_lti_jwt(self, pyramid_request, lti_v11_params):
        class ExampleSchema(LTIV11CoreSchema):
            location = "form"
            extra = marshmallow.fields.Str(required=False)

        pyramid_request.lti_params = lti_v11_params

        parsed_params = ExampleSchema(pyramid_request).parse()

        # The resulting value contains both the key from the JWT and the extra one that comes originally from request.params
        assert parsed_params == Any.dict.containing({"extra": Any.string()})

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.POST["id_token"] = "JWT"
        pyramid_request.params = {"extra": "value"}
        pyramid_request.lti_jwt = sentinel.lti_jwt
        return pyramid_request


class TestBasicLTILaunchSchema:
    def test_it_works_with_good_params(self, pyramid_request):
        pyramid_request.params["launch_presentation_return_url"] = "http://example.com"

        schema = BasicLTILaunchSchema(pyramid_request)
        params = schema.parse()

        assert params == Any.dict.containing({"resource_link_id": Any.string()})

    def test_it_allows_bad_urls_if_there_are_no_other_errors(self, pyramid_request):
        pyramid_request.params["launch_presentation_return_url"] = "goofyurl"

        schema = BasicLTILaunchSchema(pyramid_request)
        schema.parse()

        # Still alive!

    def test_ValidationError_raised_when_res_link_missing(self, pyramid_request):
        pyramid_request.params.pop("resource_link_id")

        schema = BasicLTILaunchSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_ValidationError_raised_when_res_link_missing_with_bad_return_url(
        self, pyramid_request
    ):
        pyramid_request.params.pop("resource_link_id")
        pyramid_request.params["launch_presentation_return_url"] = "broken"

        schema = BasicLTILaunchSchema(pyramid_request)

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            schema.location: {
                "launch_presentation_return_url": ["Not a valid URL."],
                "resource_link_id": ["Missing data for required field."],
            },
        }

    @pytest.mark.parametrize(
        "required_param",
        ["oauth_consumer_key", "tool_consumer_instance_guid", "user_id"],
    )
    def test_it_raises_ValidationError_if_a_non_reportable_field_is_missing(
        self, pyramid_request, required_param
    ):
        pyramid_request.params["launch_presentation_return_url"] = "http://example.com"
        del pyramid_request.params[required_param]

        schema = BasicLTILaunchSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize(
        "required_param",
        [
            "resource_link_id",
            "lti_version",
            "lti_message_type",
            "context_id",
            "context_title",
        ],
    )
    def test_it_raises_LTIToolRedirect_if_a_reportable_field_is_missing(
        self, pyramid_request, required_param
    ):
        # The LTI 1.1 certification test suite requires LTI apps to redirect to
        # the LMS with an error message if the launch request is invalid. But
        # only if there's a launch_presentation_return_url and only if certain
        # launch params are invalid, not others. For other params the test
        # suite specifically requires that you *don't* redirect back to the
        # LMS.
        pyramid_request.params["launch_presentation_return_url"] = "http://example.com"
        del pyramid_request.params[required_param]

        schema = BasicLTILaunchSchema(pyramid_request)

        with pytest.raises(LTIToolRedirect) as exc_info:
            schema.parse()

        assert (
            exc_info.value.location
            == f"http://example.com?lti_msg=Field+%27{required_param}%27%3A+Missing+data+for+required+field."
        )

    @pytest.mark.parametrize(
        "required_param",
        [
            "lis_person_name_given",
            "lis_person_name_family",
            "lis_person_name_full",
            "lis_person_contact_email_primary",
        ],
    )
    def test_it_allow_none_values(self, pyramid_request, required_param):
        pyramid_request.params[required_param] = None

        schema = BasicLTILaunchSchema(pyramid_request)

        schema.parse()

    @pytest.mark.parametrize(
        "required_param",
        [
            "resource_link_id",
            "lti_version",
            "lti_message_type",
            "context_id",
            "context_title",
        ],
    )
    def test_it_raises_ValidationError_if_a_reportable_field_is_missing_but_theres_no_launch_presentation_return_url(
        self, pyramid_request, required_param
    ):
        del pyramid_request.params[required_param]

        schema = BasicLTILaunchSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()


class TestDeepLinkingLTILaunchSchema:
    def test_it(self, schema, valid_params):
        parsed_params = schema.parse()

        for key, value in parsed_params.items():
            assert valid_params[key] == value

    @pytest.mark.parametrize(
        "missing_param",
        [
            "context_id",
            "context_title",
            "lti_message_type",
            "lti_version",
            "tool_consumer_instance_guid",
            "user_id",
            "roles",
        ],
    )
    def test_required_params(self, schema, pyramid_request, missing_param):
        del pyramid_request.params[missing_param]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            schema.location: {missing_param: ["Missing data for required field."]},
        }

    @pytest.mark.parametrize(
        "invalid_params,expected_error_messages",
        [
            (
                {"lti_version": "invalid version"},
                {"lti_version": ["Must be one of: LTI-1p0, 1.3.0."]},
            ),
            (
                {"lti_message_type": "invalid message type"},
                {
                    "lti_message_type": [
                        "Must be one of: ContentItemSelectionRequest, LtiDeepLinkingRequest."
                    ]
                },
            ),
        ],
    )
    def test_invalid_params(
        self, schema, pyramid_request, invalid_params, expected_error_messages
    ):
        pyramid_request.params.update(invalid_params)

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {schema.location: expected_error_messages}

    @pytest.fixture
    def valid_params(self, lti_v11_params):
        valid_params = dict(lti_v11_params)
        valid_params.update(
            {
                "lti_message_type": "ContentItemSelectionRequest",
                "custom_canvas_api_domain": "test_custom_canvas_api_domain",
                "custom_canvas_course_id": "test_custom_canvas_course_id",
                "launch_presentation_return_url": "test_launch_presentation_return_url",
            }
        )
        return valid_params

    @pytest.fixture
    def pyramid_request(self, pyramid_request, valid_params):
        pyramid_request.params.clear()
        pyramid_request.params.update(valid_params)
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return DeepLinkingLTILaunchSchema(pyramid_request)


class TestConfigureAssignmentSchema:
    def test_that_validation_succeeds_for_valid_requests(self, schema):
        schema.parse()

    def test_with_valid_auto_grading_config_in_json(
        self, pyramid_request, schema, auto_grading_config
    ):
        pyramid_request.params["auto_grading_config"] = json.dumps(auto_grading_config)

        data = schema.parse()

        assert data["auto_grading_config"] == auto_grading_config

    def test_with_invalid_auto_grading_config_in_json(
        self, pyramid_request, schema, auto_grading_config
    ):
        auto_grading_config["required_annotations"] = -1
        pyramid_request.params["auto_grading_config"] = json.dumps(auto_grading_config)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_with_invalid_json(self, pyramid_request, schema):
        pyramid_request.params["auto_grading_config"] = "{]"

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.fixture
    def auto_grading_config(self):
        return {
            "grading_type": "scaled",
            "activity_calculation": "separate",
            "required_annotations": 10,
            "required_replies": 5,
        }

    @pytest.fixture
    def pyramid_request(self):
        pyramid_request = testing.DummyRequest()
        pyramid_request.lti_jwt = {}
        pyramid_request.params["lti_version"] = "LTI-1p0"
        pyramid_request.params["roles"] = "INSTRUCTOR"

        pyramid_request.params["document_url"] = "test_document_url"
        pyramid_request.params["resource_link_id"] = "test_resource_link_id"
        pyramid_request.params["oauth_consumer_key"] = "test_oauth_consumer_key"
        pyramid_request.params["user_id"] = "test_user_id"
        pyramid_request.params["context_id"] = "test_context_id"
        pyramid_request.params["context_title"] = "test_context_title"
        pyramid_request.params["tool_consumer_instance_guid"] = (
            "test_tool_consumer_instance_guid"
        )
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return ConfigureAssignmentSchema(pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.content_type = "application/x-www-form-urlencoded"
    return pyramid_request
