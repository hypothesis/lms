import pytest
from h_matchers import Any

from lms.validation import (
    LaunchParamsSchema,
    LaunchParamsURLConfiguredSchema,
    LTIToolRedirect,
    ValidationError,
)


class TestLaunchParamsSchema:
    def test_it_works_with_good_params(self, pyramid_request):
        pyramid_request.params["launch_presentation_return_url"] = "http://example.com"

        schema = LaunchParamsSchema(pyramid_request)
        params = schema.parse()

        assert params == Any.dict.containing({"resource_link_id": Any.string()})

    def test_it_allows_bad_urls_if_there_are_no_other_errors(self, pyramid_request):
        pyramid_request.params["launch_presentation_return_url"] = "goofyurl"

        schema = LaunchParamsSchema(pyramid_request)
        schema.parse()

        # Still alive!

    def test_ValidationError_raised_when_res_link_missing(self, pyramid_request):
        pyramid_request.params.pop("resource_link_id")

        schema = LaunchParamsSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_ValidationError_raised_when_res_link_missing_with_bad_return_url(
        self, pyramid_request
    ):
        pyramid_request.params.pop("resource_link_id")
        pyramid_request.params["launch_presentation_return_url"] = "broken"

        schema = LaunchParamsSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_LTIToolRedirect_raised_when_res_link_missing_with_return_url(
        self, pyramid_request
    ):
        pyramid_request.params.pop("resource_link_id")
        pyramid_request.params["launch_presentation_return_url"] = "http://example.com"

        schema = LaunchParamsSchema(pyramid_request)

        with pytest.raises(LTIToolRedirect):
            schema.parse()


class TestURLConfiguredLaunchParamsSchema:
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

        assert exc_info.value.messages == Any.dict.containing(
            {"url": ["Missing data for required field."]}
        )

    @pytest.fixture
    def set_url(self, pyramid_request):
        def set_url_(url):
            pyramid_request.GET["url"] = url
            pyramid_request.POST["url"] = url

        return set_url_

    @pytest.fixture
    def schema(self, pyramid_request):
        return LaunchParamsURLConfiguredSchema(pyramid_request)


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
