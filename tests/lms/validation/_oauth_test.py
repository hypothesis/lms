import jwt
import pytest
from pyramid import testing

from lms.validation import CanvasOAuthCallbackSchema
from lms.validation import parser
from lms.validation import (
    ValidationError,
    MissingStateParamError,
    ExpiredStateParamError,
    InvalidStateParamError,
)
from lms.validation._helpers import ExpiredJWTError, InvalidJWTError, instantiate_schema
from lms.values import LTIUser


class TestCanvasOauthCallbackSchema:
    def test_state_param_encodes_lti_user_and_csrf_token_into_state_jwt(
        self, schema, secrets, _helpers, lti_user
    ):
        state = schema.state_param()

        secrets.token_hex.assert_called_once_with()
        _helpers.encode_jwt.assert_called_once_with(
            {"user": lti_user._asdict(), "csrf": secrets.token_hex.return_value},
            "test_oauth2_state_secret",
        )
        assert state == _helpers.encode_jwt.return_value

    def test_state_param_also_stashes_csrf_token_in_session(
        self, schema, secrets, pyramid_request
    ):
        del pyramid_request.session["oauth2_csrf"]

        schema.state_param()

        assert pyramid_request.session["oauth2_csrf"] == secrets.token_hex.return_value

    def test_lti_user_returns_the_lti_user_value(self, schema, _helpers, lti_user):
        returned = schema.lti_user()

        _helpers.decode_jwt.assert_called_once_with(
            "test_state", "test_oauth2_state_secret"
        )
        assert returned == lti_user

    def test_lti_user_raises_if_theres_no_state_param(self, schema, pyramid_request):
        del pyramid_request.params["state"]

        with pytest.raises(MissingStateParamError):
            schema.lti_user()

    def test_lti_user_raises_if_the_state_param_is_expired(self, schema, _helpers):
        _helpers.decode_jwt.side_effect = ExpiredJWTError()

        with pytest.raises(ExpiredStateParamError):
            schema.lti_user()

    def test_lti_user_raises_if_the_state_param_is_invalid(self, schema, _helpers):
        _helpers.decode_jwt.side_effect = InvalidJWTError()

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
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == {"code": ["Missing data for required field."]}

    def test_it_raises_if_the_state_is_missing(self, schema, pyramid_request):
        del pyramid_request.params["state"]

        with pytest.raises(ValidationError) as exc_info:
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == {
            "state": ["Missing data for required field."]
        }

    def test_it_raises_if_the_state_jwt_is_expired(
        self, schema, pyramid_request, _helpers
    ):
        _helpers.decode_jwt.side_effect = ExpiredJWTError()

        with pytest.raises(ValidationError) as exc_info:
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == {"state": ["Expired `state` parameter"]}

    def test_it_raises_if_the_state_jwt_is_invalid(
        self, schema, pyramid_request, _helpers
    ):
        _helpers.decode_jwt.side_effect = InvalidJWTError()

        with pytest.raises(ValidationError) as exc_info:
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == {"state": ["Invalid `state` parameter"]}

    def test_it_raises_if_the_csrf_token_doesnt_match_the_copy_in_the_session(
        self, schema, pyramid_request
    ):
        pyramid_request.session["oauth2_csrf"] = "wrong"

        with pytest.raises(ValidationError) as exc_info:
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == {"state": ["Invalid CSRF token"]}

    def test_it_raises_if_theres_no_csrf_token_in_the_session(
        self, schema, pyramid_request
    ):
        del pyramid_request.session["oauth2_csrf"]

        with pytest.raises(ValidationError) as exc_info:
            self.parse(schema, pyramid_request)

        assert exc_info.value.messages == {"state": ["Invalid CSRF token"]}

    def test_it_removes_the_csrf_token_from_the_session(self, schema, pyramid_request):
        self.parse(schema, pyramid_request)

        assert "oauth2_csrf" not in pyramid_request.session

    def test_it_returns_the_valid_state_and_authorization_code(
        self, schema, pyramid_request
    ):
        parsed_params = self.parse(schema, pyramid_request)

        assert parsed_params == {"code": "test_code", "state": "test_state"}

    def parse(self, schema, request):
        """Parse ``request`` with ``schema`` and return the parsed params."""
        return parser.parse(schema, request, locations=["querystring"])

    @pytest.fixture
    def schema(self, pyramid_request):
        return instantiate_schema(CanvasOAuthCallbackSchema, pyramid_request)

    @pytest.fixture
    def lti_user(self):
        return LTIUser("test_user_id", "test_oauth_consumer_key", "test_roles")

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


@pytest.fixture(autouse=True)
def secrets(patch):
    secrets = patch("lms.validation._oauth.secrets")
    secrets.token_hex.return_value = "test_csrf"
    return secrets


@pytest.fixture(autouse=True)
def _helpers(patch, lti_user):
    _helpers = patch("lms.validation._oauth._helpers")
    _helpers.decode_jwt.return_value = {"csrf": "test_csrf", "user": lti_user._asdict()}
    return _helpers
