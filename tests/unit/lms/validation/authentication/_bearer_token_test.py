import datetime

import pytest
from pyramid.testing import DummyRequest
from webargs.pyramidparser import parser

from lms.validation import ValidationError
from lms.validation.authentication import (
    BearerTokenSchema,
    ExpiredJWTError,
    ExpiredSessionTokenError,
    InvalidJWTError,
    InvalidSessionTokenError,
    MissingSessionTokenError,
)
from tests import factories


class TestBearerTokenSchema:
    def test_it_serializes_lti_users_into_bearer_tokens(self, lti_user, schema, _jwt):
        authorization_param_value = schema.authorization_param(lti_user)

        _jwt.encode_jwt.assert_called_once_with(
            lti_user._asdict(), "test_secret", lifetime=datetime.timedelta(hours=24)
        )
        assert authorization_param_value == f"Bearer {_jwt.encode_jwt.return_value}"

    def test_it_deserializes_lti_users_from_authorization_headers(
        self, lti_user, schema, _jwt
    ):
        assert schema.lti_user(location="headers") == lti_user
        _jwt.decode_jwt.assert_called_once_with(
            _jwt.encode_jwt.return_value, "test_secret"
        )

    def test_it_deserializes_lti_users_from_authorization_query_params(
        self, lti_user, pyramid_request, schema
    ):
        # You can also put the authorization param in the query string, instead
        # of in the headers.
        pyramid_request.params["authorization"] = pyramid_request.headers[
            "authorization"
        ]
        del pyramid_request.headers["authorization"]

        assert schema.lti_user(location="query") == lti_user

    def test_it_raises_if_theres_no_authorization_param(self, schema, pyramid_request):
        del pyramid_request.headers["authorization"]

        with pytest.raises(MissingSessionTokenError) as exc_info:
            schema.lti_user(location="headers")

        assert exc_info.value.messages == {
            "headers": {"authorization": ["Missing data for required field."]},
        }

    def test_it_raises_if_the_jwt_has_expired(self, schema, _jwt):
        _jwt.decode_jwt.side_effect = ExpiredJWTError()

        with pytest.raises(ExpiredSessionTokenError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {
            "headers": {"authorization": ["Expired session token"]}
        }

    def test_it_raises_if_the_jwt_is_invalid(self, schema, _jwt):
        _jwt.decode_jwt.side_effect = InvalidJWTError()

        with pytest.raises(InvalidSessionTokenError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {
            "headers": {"authorization": ["Invalid session token"]}
        }

    def test_it_raises_if_the_user_id_param_is_missing(self, schema, _jwt):
        del _jwt.decode_jwt.return_value["user_id"]

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {
            "headers": {"user_id": ["Missing data for required field."]},
        }

    def test_it_raises_if_the_oauth_consumer_key_param_is_missing(self, schema, _jwt):
        del _jwt.decode_jwt.return_value["oauth_consumer_key"]

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {
            "headers": {"oauth_consumer_key": ["Missing data for required field."]},
        }

    def test_it_raises_if_the_roles_param_is_missing(self, schema, _jwt):
        del _jwt.decode_jwt.return_value["roles"]

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {
            "headers": {"roles": ["Missing data for required field."]},
        }

    def test_serialize_and_deserialize_via_marshmallow_api(self, lti_user, schema):
        serialized = schema.dump(lti_user)
        deserialized = schema.load(serialized)

        assert deserialized == lti_user

    def test_parse_via_webargs_api(self, lti_user, schema, pyramid_request):
        deserialized = parser.parse(schema, pyramid_request, location="headers")

        assert deserialized == lti_user

    @pytest.fixture
    def schema(self, pyramid_request):
        """Return a BearerTokenSchema configured with the right secret."""
        return BearerTokenSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, _jwt):
        pyramid_request = DummyRequest()
        pyramid_request.headers[
            "authorization"
        ] = f"Bearer {_jwt.encode_jwt.return_value}"
        return pyramid_request


@pytest.fixture(autouse=True)
def _jwt(patch, lti_user):
    _jwt = patch("lms.validation.authentication._bearer_token._jwt")
    _jwt.encode_jwt.return_value = "ENCODED_JWT"
    _jwt.decode_jwt.return_value = lti_user._asdict()
    return _jwt


@pytest.fixture
def lti_user():
    """Return the original LTIUser that was encoded as a JWT in the request."""
    return factories.LTIUser()
