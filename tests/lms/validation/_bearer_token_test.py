import datetime
import json

import pytest
from webargs.pyramidparser import parser
from pyramid.testing import DummyRequest

from lms.validation import (
    BearerTokenSchema,
    ValidationError,
    ExpiredSessionTokenError,
    MissingSessionTokenError,
    InvalidSessionTokenError,
)
from lms.validation import _helpers
from lms.validation._helpers import ExpiredJWTError, InvalidJWTError
from lms.values import LTIUser


class TestBearerTokenSchema:
    def test_it_serializes_lti_users_into_bearer_tokens(
        self, lti_user, schema, _helpers
    ):
        authorization_param_value = schema.authorization_param(lti_user)

        _helpers.encode_jwt.assert_called_once_with(lti_user._asdict(), "test_secret")
        assert authorization_param_value == f"Bearer {_helpers.encode_jwt.return_value}"

    def test_it_deserializes_lti_users_from_authorization_headers(
        self, lti_user, schema, _helpers
    ):
        assert schema.lti_user() == lti_user
        _helpers.decode_jwt.assert_called_once_with(
            _helpers.encode_jwt.return_value, "test_secret"
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

        assert schema.lti_user() == lti_user

    def test_it_raises_if_theres_no_authorization_param(self, schema, pyramid_request):
        del pyramid_request.headers["authorization"]

        with pytest.raises(MissingSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "authorization": ["Missing data for required field."]
        }

    def test_it_raises_if_the_jwt_has_expired(self, schema, _helpers):
        _helpers.decode_jwt.side_effect = ExpiredJWTError()

        with pytest.raises(ExpiredSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Expired session token"]}

    def test_it_raises_if_the_jwt_is_invalid(self, schema, _helpers):
        _helpers.decode_jwt.side_effect = InvalidJWTError()

        with pytest.raises(InvalidSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Invalid session token"]}

    def test_it_raises_if_the_user_id_param_is_missing(self, schema, _helpers):
        del _helpers.decode_jwt.return_value["user_id"]

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "user_id": ["Missing data for required field."]
        }

    def test_it_raises_if_the_oauth_consumer_key_param_is_missing(
        self, schema, _helpers
    ):
        del _helpers.decode_jwt.return_value["oauth_consumer_key"]

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "oauth_consumer_key": ["Missing data for required field."]
        }

    def test_serialize_and_deserialize_via_marshmallow_api(self, lti_user, schema):
        serialized = schema.dump(lti_user)
        deserialized = schema.load(serialized.data)

        assert deserialized.data == lti_user

    def test_parse_via_webargs_api(self, lti_user, schema, pyramid_request):
        deserialized = parser.parse(schema, pyramid_request, locations=["headers"])

        assert deserialized == lti_user

    @pytest.fixture
    def lti_user(self):
        """The original LTIUser that was encoded as a JWT in the request."""
        return LTIUser(
            user_id="TEST_USER_ID", oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY"
        )

    @pytest.fixture
    def schema(self, pyramid_request):
        """A BearerTokenSchema configured with the right secret."""
        return BearerTokenSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, _helpers):
        pyramid_request = DummyRequest()
        pyramid_request.headers[
            "authorization"
        ] = f"Bearer {_helpers.encode_jwt.return_value}"
        return pyramid_request


@pytest.fixture(autouse=True)
def _helpers(patch):
    _helpers = patch("lms.validation._bearer_token._helpers")
    _helpers.encode_jwt.return_value = "ENCODED_JWT"
    _helpers.decode_jwt.return_value = {
        "user_id": "TEST_USER_ID",
        "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
    }
    return _helpers
