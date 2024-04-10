import datetime

import pytest

from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.validation import ValidationError
from lms.validation.authentication import BearerTokenSchema


class TestBearerTokenSchema:
    def test_it_serializes_lti_users_into_bearer_tokens(
        self, lti_user, schema, jwt_service, lti_user_service
    ):
        authorization_param_value = schema.authorization_param(lti_user)

        lti_user_service.serialize.assert_called_once_with(lti_user)
        jwt_service.encode_with_secret.assert_called_once_with(
            lti_user_service.serialize.return_value,
            "test_secret",
            lifetime=datetime.timedelta(hours=24),
        )
        assert (
            authorization_param_value
            == f"Bearer {jwt_service.encode_with_secret.return_value}"
        )

    def test_it_deserializes_lti_users_from_authorization_headers(
        self, schema, jwt_service, lti_user_service
    ):
        assert (
            schema.lti_user(location="headers")
            == lti_user_service.deserialize.return_value
        )
        jwt_service.decode_with_secret.assert_called_once_with(
            jwt_service.encode_with_secret.return_value, "test_secret"
        )

    def test_it_deserializes_lti_users_from_authorization_query_params(
        self, pyramid_request, schema, lti_user_service
    ):
        # You can also put the authorization param in the query string, instead
        # of in the headers.
        pyramid_request.params["authorization"] = pyramid_request.headers[
            "authorization"
        ]
        del pyramid_request.headers["authorization"]

        assert (
            schema.lti_user(location="query")
            == lti_user_service.deserialize.return_value
        )

    def test_it_allows_bearer_preffix_missing(self, schema, pyramid_request):
        pyramid_request.headers["authorization"] = pyramid_request.headers[
            "authorization"
        ].replace("Bearer ", "")

        assert schema.lti_user(location="headers")

    def test_it_raises_if_theres_no_authorization_param(self, schema, pyramid_request):
        del pyramid_request.headers["authorization"]

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user(location="headers")

        assert exc_info.value.messages == {
            "authorization": ["Missing data for required field."]
        }

    def test_it_raises_if_the_jwt_has_expired(self, schema, jwt_service):
        jwt_service.decode_with_secret.side_effect = ExpiredJWTError()

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {"authorization": ["Expired session token"]}

    def test_it_raises_if_the_jwt_is_invalid(self, schema, jwt_service):
        jwt_service.decode_with_secret.side_effect = InvalidJWTError()

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user("headers")

        assert exc_info.value.messages == {"authorization": ["Invalid session token"]}

    @pytest.fixture
    def schema(self, pyramid_request):
        """Return a BearerTokenSchema configured with the right secret."""
        return BearerTokenSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.headers["authorization"] = "Bearer ENCODED_JWT"
        return pyramid_request

    @pytest.fixture(autouse=True)
    def jwt_service(self, jwt_service, lti_user_service):
        jwt_service.decode_with_secret.return_value = (
            lti_user_service.serialize.return_value
        )
        jwt_service.encode_with_secret.return_value = "ENCODED_JWT"

        return jwt_service
