import datetime
import json
import jwt

import pytest
from webargs.pyramidparser import parser

from lms.validation import (
    BearerTokenSchema,
    ValidationError,
    ExpiredSessionTokenError,
    MissingSessionTokenError,
    InvalidSessionTokenError,
)
from lms.values import LTIUser


class TestBearerTokenSchema:
    def test_it_serializes_lti_users_to_bearer_tokens(self, lti_user, schema):
        authorization_param_value = schema.authorization_param(lti_user)

        assert authorization_param_value.startswith("Bearer ")

    def test_it_deserializes_lti_users_from_authorization_headers(
        self, authorization_param, lti_user, pyramid_request, schema
    ):
        pyramid_request.headers["authorization"] = authorization_param

        deserialized_lti_user = schema.lti_user()

        assert deserialized_lti_user == lti_user

    def test_it_raises_if_theres_no_authorization_param(self, schema):
        with pytest.raises(MissingSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "authorization": ["Missing data for required field."]
        }

    def test_it_raises_if_the_authorization_param_has_the_wrong_format(
        self, authorization_param, pyramid_request, schema
    ):
        # Does not being with "Bearer ":
        pyramid_request.headers["authorization"] = authorization_param[len("Bearer ") :]

        with pytest.raises(InvalidSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Invalid session token"]}

    def test_it_raises_if_the_jwt_is_encoded_with_the_wrong_secret(
        self, pyramid_request, lti_user, schema
    ):
        wrongly_encoded_jwt = self.encode_jwt(lti_user._asdict(), secret="WRONG_SECRET")
        pyramid_request.headers["authorization"] = "Bearer " + wrongly_encoded_jwt

        with pytest.raises(InvalidSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Invalid session token"]}

    def test_it_raises_if_the_jwt_is_encoded_with_the_wrong_algorithm(
        self, pyramid_request, lti_user, schema
    ):
        wrongly_encoded_jwt = self.encode_jwt(lti_user._asdict(), algorithm="HS384")
        pyramid_request.headers["authorization"] = "Bearer " + wrongly_encoded_jwt

        with pytest.raises(InvalidSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Invalid session token"]}

    def test_it_raises_if_the_jwt_has_expired(self, lti_user, pyramid_request, schema):
        five_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        payload = lti_user._asdict()
        payload["exp"] = five_minutes_ago
        expired_jwt = self.encode_jwt(payload)
        pyramid_request.headers["authorization"] = "Bearer " + expired_jwt

        with pytest.raises(ExpiredSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Expired session token"]}

    def test_it_raises_if_the_jwt_has_no_expiry_time(
        self, lti_user, pyramid_request, schema
    ):
        jwt_with_no_expiry_time = self.encode_jwt(lti_user._asdict(), omit_exp=True)
        pyramid_request.headers["authorization"] = "Bearer " + jwt_with_no_expiry_time

        with pytest.raises(InvalidSessionTokenError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {"authorization": ["Invalid session token"]}

    def test_it_raises_if_the_user_id_param_is_missing(
        self, lti_user, pyramid_request, schema
    ):
        payload = lti_user._asdict()
        del payload["user_id"]
        jwt_with_no_user_id = self.encode_jwt(payload)
        pyramid_request.headers["authorization"] = "Bearer " + jwt_with_no_user_id

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "user_id": ["Missing data for required field."]
        }

    def test_it_raises_if_the_oauth_consumer_key_param_is_missing(
        self, lti_user, pyramid_request, schema
    ):
        payload = lti_user._asdict()
        del payload["oauth_consumer_key"]
        jwt_with_no_user_id = self.encode_jwt(payload)
        pyramid_request.headers["authorization"] = "Bearer " + jwt_with_no_user_id

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "oauth_consumer_key": ["Missing data for required field."]
        }

    def test_serialize_and_deserialize_via_marshmallow_api(self, lti_user, schema):
        serialized = schema.dump(lti_user)
        deserialized = schema.load(serialized.data)

        assert deserialized.data == lti_user

    def test_parse_via_webargs_api(
        self, lti_user, schema, pyramid_request, authorization_param
    ):
        pyramid_request.headers["authorization"] = authorization_param

        deserialized = parser.parse(schema, pyramid_request, locations=["headers"])

        assert deserialized == lti_user

    def encode_jwt(self, payload, omit_exp=False, secret=None, algorithm=None):
        if not omit_exp:
            # Insert an unexpired expiry time into the given payload dict, if
            # it doesn't already contain an expiry time.
            payload.setdefault(
                "exp", datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            )

        jwt_bytes = jwt.encode(
            payload, secret or "test_secret", algorithm=algorithm or "HS256"
        )
        # PyJWT returns JWT's as UTF8-encoded byte strings (this isn't
        # documented, but see
        # https://github.com/jpadilla/pyjwt/blob/ed28e495f937f50165a252fd5696a82942cd83a7/jwt/api_jwt.py#L62).
        # We need a unicode string, so decode it.
        jwt_str = jwt_bytes.decode("utf-8")
        return jwt_str

    @pytest.fixture
    def lti_user(self):
        """The original LTIUser that was encoded as a JWT in the request."""
        return LTIUser(
            user_id="TEST_USER_ID", oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY"
        )

    @pytest.fixture
    def authorization_param(self, lti_user, pyramid_request):
        """An authorization param correctly encoded with the right secret."""
        # We use BearerTokenSchema's own ``authorization_param()`` here so
        # that the tests are also testing that a BearerTokenSchema can
        # decode the values that were encoded by another BearerTokenSchema
        # and return the original value.
        return BearerTokenSchema(pyramid_request).authorization_param(lti_user)

    @pytest.fixture
    def schema(self, pyramid_request):
        """A BearerTokenSchema configured with the right secret."""
        return BearerTokenSchema(pyramid_request)
