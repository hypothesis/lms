import pytest

from lms.validation import LaunchParamsURLConfiguredSchema, ValidationError


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
        return LaunchParamsURLConfiguredSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.content_type = "application/x-www-form-urlencoded"
        return pyramid_request
