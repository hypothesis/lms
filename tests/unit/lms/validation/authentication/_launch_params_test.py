import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.models import LTIUser
from lms.services import LTILaunchVerificationError
from lms.validation import ValidationError
from lms.validation.authentication import LaunchParamsAuthSchema


class TestLaunchParamsAuthSchema:
    def test_it_returns_the_lti_user_info(self, schema, display_name):
        lti_user = schema.lti_user()

        display_name.assert_called_once_with(
            "TEST_GIVEN_NAME", "TEST_FAMILY_NAME", "TEST_FULL_NAME"
        )
        assert lti_user == LTIUser(
            user_id="TEST_USER_ID",
            oauth_consumer_key="TEST_OAUTH_CONSUMER_KEY",
            roles="TEST_ROLES",
            tool_consumer_instance_guid="TEST_TOOL_CONSUMER_INSTANCE_GUID",
            display_name=display_name.return_value,
        )

    @pytest.mark.usefixtures("no_user_info")
    def test_user_info_fields_default_to_empty_strings(self, schema, display_name):
        schema.lti_user()

        display_name.assert_called_once_with("", "", "")

    def test_it_does_oauth_1_verification(self, launch_verifier, schema):
        schema.lti_user()

        launch_verifier.verify.assert_called_once_with()

    def test_it_raises_if_oauth_1_verification_fails(self, launch_verifier, schema):
        launch_verifier.verify.side_effect = LTILaunchVerificationError("Failed")

        with pytest.raises(ValidationError) as exc_info:
            schema.lti_user()

        assert exc_info.value.messages == {
            "form": {"_schema": ["Invalid OAuth 1 signature."]}
        }

    @pytest.mark.parametrize(
        "missing_param",
        [
            "user_id",
            "roles",
            "tool_consumer_instance_guid",
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

        assert exc_info.value.messages == {
            "form": {missing_param: ["Missing data for required field."]},
        }

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
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "lis_person_name_given": "TEST_GIVEN_NAME",
            "lis_person_name_family": "TEST_FAMILY_NAME",
            "lis_person_name_full": "TEST_FULL_NAME",
        }
        return pyramid_request

    @pytest.fixture
    def no_user_info(self, pyramid_request):
        del pyramid_request.POST["lis_person_name_given"]
        del pyramid_request.POST["lis_person_name_family"]
        del pyramid_request.POST["lis_person_name_full"]


pytestmark = pytest.mark.usefixtures("launch_verifier")


@pytest.fixture(autouse=True)
def display_name(patch):
    return patch("lms.validation.authentication._launch_params.display_name")
