import pytest
from h_matchers import Any

from lms.validation import (
    BasicLTILaunchSchema,
    ContentItemSelectionLTILaunchSchema,
    LTIToolRedirect,
    URLConfiguredBasicLTILaunchSchema,
    ValidationError,
)


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
            "launch_presentation_return_url": ["Not a valid URL."],
            "resource_link_id": ["Missing data for required field."],
        }

    def test_LTIToolRedirect_raised_when_res_link_missing_with_return_url(
        self, pyramid_request
    ):
        pyramid_request.params.pop("resource_link_id")
        pyramid_request.params["launch_presentation_return_url"] = "http://example.com"

        schema = BasicLTILaunchSchema(pyramid_request)

        with pytest.raises(LTIToolRedirect):
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

        assert exc_info.value.messages == dict(
            [("url", ["Missing data for required field."])]
        )

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
    def test_it(self, schema):
        parsed_params = schema.parse()

        assert parsed_params == {
            "context_id": "test_context_id",
            "context_title": "test_context_title",
            "lti_message_type": "ContentItemSelectionRequest",
            "lti_version": "LTI-1p0",
            "oauth_consumer_key": "test_oauth_consumer_key",
            "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
            "user_id": "test_user_id",
            "custom_canvas_api_domain": "test_custom_canvas_api_domain",
            "custom_canvas_course_id": "test_custom_canvas_course_id",
            "launch_presentation_return_url": "test_launch_presentation_return_url",
            "lis_person_name_full": "test_lis_person_name_full",
            "lis_person_name_family": "test_lis_person_name_family",
            "lis_person_name_given": "test_lis_person_name_given",
            "tool_consumer_info_product_family_code": "test_tool_consumer_info_product_family_code",
        }

    @pytest.mark.parametrize(
        "missing_param",
        [
            "context_id",
            "context_title",
            "lti_message_type",
            "lti_version",
            "oauth_consumer_key",
            "tool_consumer_instance_guid",
            "user_id",
        ],
    )
    def test_required_params(self, schema, pyramid_request, missing_param):
        del pyramid_request.params[missing_param]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == dict(
            ((missing_param, ["Missing data for required field."]),)
        )

    @pytest.mark.parametrize(
        "invalid_params,expected_error_messages",
        [
            (
                {"lti_version": "invalid version",},
                {"lti_version": ["Must be one of: LTI-1p0."]},
            ),
            (
                {"lti_message_type": "invalid message type",},
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

        assert exc_info.value.messages == expected_error_messages

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params.clear()
        pyramid_request.params.update(
            {
                "context_id": "test_context_id",
                "context_title": "test_context_title",
                "lti_message_type": "ContentItemSelectionRequest",
                "lti_version": "LTI-1p0",
                "oauth_consumer_key": "test_oauth_consumer_key",
                "tool_consumer_instance_guid": "test_tool_consumer_instance_guid",
                "user_id": "test_user_id",
                "custom_canvas_api_domain": "test_custom_canvas_api_domain",
                "custom_canvas_course_id": "test_custom_canvas_course_id",
                "launch_presentation_return_url": "test_launch_presentation_return_url",
                "lis_person_name_full": "test_lis_person_name_full",
                "lis_person_name_family": "test_lis_person_name_family",
                "lis_person_name_given": "test_lis_person_name_given",
                "tool_consumer_info_product_family_code": "test_tool_consumer_info_product_family_code",
            }
        )
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return ContentItemSelectionLTILaunchSchema(pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.content_type = "application/x-www-form-urlencoded"
    pyramid_request.params.update(
        {
            "resource_link_id": "DUMMY-LINK",
            "lti_version": "LTI-1p0",
            "lti_message_type": "basic-lti-launch-request",
            "context_id": "DUMMY-CONTEXT-ID",
            "context_title": "A context title",
        }
    )

    return pyramid_request
