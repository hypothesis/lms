from unittest.mock import sentinel

import marshmallow
import pytest
from h_matchers import Any
from pyramid import testing

from lms.validation import (
    BasicLTILaunchSchema,
    ConfigureAssignmentSchema,
    ContentItemSelectionLTILaunchSchema,
    LTIToolRedirect,
    LTIV11CoreSchema,
    URLConfiguredBasicLTILaunchSchema,
    ValidationError,
)


class TestLTIV11CoreSchema:
    def test_with_lti_jwt(self, pyramid_request, LTIParams, lti_v11_params):
        class ExampleSchema(LTIV11CoreSchema):
            location = "form"
            extra = marshmallow.fields.Str(required=False)

        LTIParams.from_v13.return_value = lti_v11_params

        parsed_params = ExampleSchema(pyramid_request).parse()

        LTIParams.from_v13.assert_called_once_with(pyramid_request.lti_jwt)
        # The resulting value contains both the key from the JWT and the extra one that comes originally from request.params
        assert parsed_params == Any.dict.containing({"extra": Any.string()})

    @pytest.fixture
    def LTIParams(self, patch):
        return patch("lms.validation._lti_launch_params.LTIParams")

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
            "form": {
                "launch_presentation_return_url": ["Not a valid URL."],
                "resource_link_id": ["Missing data for required field."],
            },
        }

    @pytest.mark.parametrize(
        "required_param",
        ["oauth_consumer_key", "user_id"],
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


class TestURLConfiguredBasicLTILaunchSchema:
    @pytest.mark.parametrize(
        "url_param, expected_parsed_url",
        [
            (
                "https%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "https://example.com/path?param=value",
            ),
            (
                "http%3A%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "http://example.com/path?param=value",
            ),
            (
                "http%3a%2F%2Fexample.com%2Fpath%3Fparam%3Dvalue",
                "http://example.com/path?param=value",
            ),
            (
                "canvas%3A%2F%2Ffile%2Fcourse_id%2FCOURSE_ID%2Ffile_if%2FFILE_ID",
                "canvas://file/course_id/COURSE_ID/file_if/FILE_ID",
            ),
        ],
    )
    def test_it_decodes_url_if_percent_encoded(
        self, schema, set_url, url_param, expected_parsed_url
    ):
        set_url(url_param)
        params = schema.parse()
        assert params["url"] == expected_parsed_url

    @pytest.mark.parametrize(
        "url_param",
        [
            "https://example.com/path?param=value",
            "http://example.com/path?param=%25foo%25",
        ],
    )
    def test_it_doesnt_decode_url_if_not_percent_encoded(
        self, schema, set_url, url_param
    ):
        set_url(url_param)
        params = schema.parse()
        assert params["url"] == url_param

    def test_it_raises_if_url_not_present(self, schema):
        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "form": {"url": ["Missing data for required field."]},
        }

    @pytest.fixture
    def set_url(self, pyramid_request):
        def set_url_(url):
            pyramid_request.GET["url"] = url
            pyramid_request.POST["url"] = url

        return set_url_

    @pytest.fixture
    def schema(self, pyramid_request):
        return URLConfiguredBasicLTILaunchSchema(pyramid_request)


class TestContentItemSelectionLTILaunchSchema:
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
            "user_id",
            "roles",
        ],
    )
    def test_required_params(self, schema, pyramid_request, missing_param):
        del pyramid_request.params[missing_param]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "form": {missing_param: ["Missing data for required field."]},
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
                {"lti_message_type": ["Must be one of: ContentItemSelectionRequest."]},
            ),
        ],
    )
    def test_invalid_params(
        self, schema, pyramid_request, invalid_params, expected_error_messages
    ):
        pyramid_request.params.update(invalid_params)

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"form": expected_error_messages}

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
        return ContentItemSelectionLTILaunchSchema(pyramid_request)


class TestConfigureAssignmentSchema:
    def test_that_validation_succeeds_for_valid_requests(self, schema):
        schema.parse()

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
        pyramid_request.params[
            "tool_consumer_instance_guid"
        ] = "test_tool_consumer_instance_guid"
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return ConfigureAssignmentSchema(pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.content_type = "application/x-www-form-urlencoded"
    return pyramid_request
