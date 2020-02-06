from unittest import mock

import pytest
import requests
from pyramid import testing

from lms.validation import ValidationError
from lms.validation.authentication import (
    ExpiredJWTError,
    ExpiredStateParamError,
    InvalidJWTError,
    InvalidStateParamError,
    MissingStateParamError,
)
from lms.validation.authentication._oauth import (
    CanvasAccessTokenResponseSchema,
    CanvasOAuthCallbackSchema,
    CanvasRefreshTokenResponseSchema,
)
from lms.values import LTIUser


class TestCanvasOauthCallbackSchema:
    def test_state_param_encodes_lti_user_and_csrf_token_into_state_jwt(
        self, schema, secrets, _jwt, lti_user
    ):
        state = schema.state_param()

        secrets.token_hex.assert_called_once_with()
        _jwt.encode_jwt.assert_called_once_with(
            {"user": lti_user._asdict(), "csrf": secrets.token_hex.return_value},
            "test_oauth2_state_secret",
        )
        assert state == _jwt.encode_jwt.return_value

    def test_state_param_also_stashes_csrf_token_in_session(
        self, schema, secrets, pyramid_request
    ):
        del pyramid_request.session["oauth2_csrf"]

        schema.state_param()

        assert pyramid_request.session["oauth2_csrf"] == secrets.token_hex.return_value

    def test_lti_user_returns_the_lti_user_value(self, schema, _jwt, lti_user):
        returned = schema.lti_user()

        _jwt.decode_jwt.assert_called_once_with(
            "test_state", "test_oauth2_state_secret"
        )
        assert returned == lti_user

    def test_lti_user_raises_if_theres_no_state_param(self, schema, pyramid_request):
        del pyramid_request.params["state"]

        with pytest.raises(MissingStateParamError):
            schema.lti_user()

    def test_lti_user_raises_if_the_state_param_is_expired(self, schema, _jwt):
        _jwt.decode_jwt.side_effect = ExpiredJWTError()

        with pytest.raises(ExpiredStateParamError):
            schema.lti_user()

    def test_lti_user_raises_if_the_state_param_is_invalid(self, schema, _jwt):
        _jwt.decode_jwt.side_effect = InvalidJWTError()

        with pytest.raises(InvalidStateParamError):
            schema.lti_user()

    def test_lti_doesnt_remove_the_csrf_token_from_the_session(
        self, schema, pyramid_request, secrets
    ):
        schema.lti_user()

        assert pyramid_request.session["oauth2_csrf"] == secrets.token_hex.return_value

    def test_it_raises_if_the_authorization_code_is_missing(
        self, schema, pyramid_request
    ):
        del pyramid_request.params["code"]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"code": ["Missing data for required field."]}

    def test_it_raises_if_the_state_is_missing(self, schema, pyramid_request):
        del pyramid_request.params["state"]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "state": ["Missing data for required field."]
        }

    def test_it_raises_if_the_state_jwt_is_expired(self, schema, pyramid_request, _jwt):
        _jwt.decode_jwt.side_effect = ExpiredJWTError()

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"state": ["Expired `state` parameter"]}

    def test_it_raises_if_the_state_jwt_is_invalid(self, schema, pyramid_request, _jwt):
        _jwt.decode_jwt.side_effect = InvalidJWTError()

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"state": ["Invalid `state` parameter"]}

    def test_it_raises_if_the_csrf_token_doesnt_match_the_copy_in_the_session(
        self, schema, pyramid_request
    ):
        pyramid_request.session["oauth2_csrf"] = "wrong"

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"state": ["Invalid CSRF token"]}

    def test_it_raises_if_theres_no_csrf_token_in_the_session(
        self, schema, pyramid_request
    ):
        del pyramid_request.session["oauth2_csrf"]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"state": ["Invalid CSRF token"]}

    def test_it_removes_the_csrf_token_from_the_session(self, schema, pyramid_request):
        schema.parse()

        assert "oauth2_csrf" not in pyramid_request.session

    def test_it_returns_the_valid_state_and_authorization_code(
        self, schema, pyramid_request
    ):
        parsed_params = schema.parse()

        assert parsed_params == {"code": "test_code", "state": "test_state"}

    @pytest.fixture
    def schema(self, pyramid_request):
        return CanvasOAuthCallbackSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, lti_user):
        """Return a minimal valid OAuth 2 redirect request."""
        pyramid_request = testing.DummyRequest()
        pyramid_request.params["code"] = "test_code"
        pyramid_request.params["state"] = "test_state"
        pyramid_request.session["oauth2_csrf"] = "test_csrf"
        pyramid_request.lti_user = lti_user
        pyramid_request.registry.settings = {
            "oauth2_state_secret": "test_oauth2_state_secret"
        }
        return pyramid_request

    @pytest.fixture
    def pyramid_config(self, pyramid_request):
        # Override the global pyramid_config fixture with the minimum needed to
        # make this test class pass.
        settings = {"oauth2_state_secret": "test_oauth2_state_secret"}
        with testing.testConfig(request=pyramid_request, settings=settings) as config:
            config.include("pyramid_services")
            yield config


class TestCanvasAccessTokenResponseSchema:
    def test_it_returns_the_valid_parsed_params(self, schema, response):
        parsed_params = schema.parse()

        assert parsed_params == {
            "access_token": "TEST_ACCESS_TOKEN",
            "refresh_token": "TEST_REFRESH_TOKEN",
            "expires_in": 3600,
        }

    def test_access_token_is_required(self, schema, response):
        del response.json.return_value["access_token"]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "access_token": ["Missing data for required field."]
        }

    def test_refresh_token_is_optional(self, schema, response):
        del response.json.return_value["refresh_token"]

        parsed_params = schema.parse()

        assert parsed_params == {
            "access_token": "TEST_ACCESS_TOKEN",
            "expires_in": 3600,
        }

    def test_expires_in_is_optional(self, schema, response):
        del response.json.return_value["expires_in"]

        parsed_params = schema.parse()

        assert parsed_params == {
            "access_token": "TEST_ACCESS_TOKEN",
            "refresh_token": "TEST_REFRESH_TOKEN",
        }

    @pytest.mark.parametrize("invalid_expires_in_value", ["foo", -16, False, None])
    def test_expires_in_must_be_an_int_greater_than_0(
        self, invalid_expires_in_value, schema, response
    ):
        response.json.return_value["expires_in"] = invalid_expires_in_value

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert list(exc_info.value.messages.keys()) == ["expires_in"]

    @pytest.fixture
    def response(self):
        """The ``requests`` library response that's being validated."""
        response = mock.create_autospec(requests.Response, instance=True, spec_set=True)
        response.json.return_value = {
            "access_token": "TEST_ACCESS_TOKEN",
            "refresh_token": "TEST_REFRESH_TOKEN",
            "expires_in": 3600,
        }
        return response

    @pytest.fixture
    def schema(self, response):
        return CanvasAccessTokenResponseSchema(response)


class TestCanvasRefreshTokenResponseSchema(TestCanvasAccessTokenResponseSchema):
    @pytest.fixture
    def schema(self, response):
        return CanvasRefreshTokenResponseSchema(response)


@pytest.fixture(autouse=True)
def secrets(patch):
    secrets = patch("lms.validation.authentication._oauth.secrets")
    secrets.token_hex.return_value = "test_csrf"
    return secrets


@pytest.fixture(autouse=True)
def _jwt(patch, lti_user):
    _jwt = patch("lms.validation.authentication._oauth._jwt")
    _jwt.decode_jwt.return_value = {"csrf": "test_csrf", "user": lti_user._asdict()}
    return _jwt


@pytest.fixture
def lti_user():
    return LTIUser("test_user_id", "test_oauth_consumer_key", "test_roles")
