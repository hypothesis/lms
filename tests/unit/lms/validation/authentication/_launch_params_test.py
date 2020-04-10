import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.models import LTIUser
from lms.services import LTILaunchVerificationError
from lms.validation import ValidationError
from lms.validation.authentication import LaunchParamsAuthSchema


class TestLaunchParamsAuthSchema:
    def test_it_returns_the_lti_user_info(self, schema):
        lti_user = schema.lti_user()

        assert lti_user == LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", "TEST_ROLES"
        )

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
        return LaunchParamsAuthSchema(pyramid_request)

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


pytestmark = pytest.mark.usefixtures("launch_verifier")
