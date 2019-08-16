import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.services import LTILaunchVerificationError
from lms.validation import (
    LaunchParamsSchema,
    ValidationError,
    URLConfiguredLaunchParamsSchema,
)
from lms.values import LTIUser


class TestLaunchParamsSchema:
    def test_it_returns_the_lti_user_info(self, schema):
        lti_user = schema.lti_user()

        assert lti_user == LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES"
        )

    def test_it_uses_assignment_oauth_consumer_key(self, schema, pyramid_request):
        # Specify a consumer key override for a SpeedGrader LTI launch.
        pyramid_request.params.update(
            {"assignment_oauth_consumer_key": "different_key"}
        )

        lti_user = schema.lti_user()

        assert lti_user.oauth_consumer_key == "different_key"

    def test_it_does_oauth_1_verification(self, launch_verifier, schema):
        schema.lti_user()

        launch_verifier.verify.assert_called_once_with()

    def test_it_raises_if_oauth_1_verification_fails(self, launch_verifier, schema):
        launch_verifier.verify.side_effect = LTILaunchVerificationError("Failed")

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"_schema": ["Invalid OAuth 1 signature."]}

    @pytest.mark.parametrize(
        "missing_param",
        [
            "user_id",
            "roles",
            "oauth_consumer_key",
            "oauth_nonce",
            "oauth_signature",
            "oauth_signature_method",
            "oauth_timestamp",
            "oauth_version",
        ],
    )
    def test_it_raises_if_a_required_param_is_missing(
        self, missing_param, pyramid_request, schema
    ):
        del pyramid_request.POST[missing_param]

        with pytest.raises(HTTPUnprocessableEntity) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == dict(
            [(missing_param, ["Missing data for required field."])]
        )

    @pytest.fixture
    def schema(self, pyramid_request):
        return LaunchParamsSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.content_type = "application/x-www-form-urlencoded"
        pyramid_request.POST = {
            "user_id": "TEST_USER_ID",
            "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            "oauth_nonce": "TEST_OAUTH_NONCE",
            "oauth_signature": "TEST_OAUTH_SIGNATURE",
            "oauth_signature_method": "TEST_OAUTH_SIGNATURE_METHOD",
            "oauth_timestamp": "TEST_OAUTH_TIMESTAMP",
            "oauth_version": "TEST_OAUTH_VERSION",
            "roles": "TEST_ROLES",
        }
        return pyramid_request


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
        return URLConfiguredLaunchParamsSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.content_type = "application/x-www-form-urlencoded"
        return pyramid_request
