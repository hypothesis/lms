from unittest.mock import sentinel

import marshmallow
import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.services import ApplicationInstanceNotFound, LTILaunchVerificationError
from lms.validation._exceptions import ValidationError
from lms.validation.authentication import LTI11AuthSchema, LTI13AuthSchema

pytestmark = pytest.mark.usefixtures("launch_verifier", "application_instance_service")


class TestLTI11AuthSchema:
    def test_it_returns_the_lti_user_info(
        self, schema, application_instance_service, LTIUser
    ):
        lti_user = schema.lti_user()

        LTIUser.from_auth_params.assert_called_once_with(
            application_instance_service.get_by_consumer_key.return_value,
            {
                "oauth_signature_method": "SHA256",
                "lis_person_name_family": "TEST_FAMILY_NAME",
                "lis_person_contact_email_primary": "test_lis_person_contact_email_primary",
                "oauth_nonce": "TEST_NONCE",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                "lis_person_name_full": "TEST_FULL_NAME",
                "oauth_version": "1p0p0",
                "lis_person_name_given": "TEST_GIVEN_NAME",
                "oauth_signature": "TEST_OAUTH_SIGNATURE",
                "roles": "Instructor",
                "tool_consumer_instance_guid": "TEST_GUID",
                "user_id": "TEST_USER_ID",
                "oauth_timestamp": "TEST_TIMESTAMP",
            },
        )
        assert lti_user == LTIUser.from_auth_params.return_value

    def test_it_raises_missing_application_instance(
        self, schema, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        with pytest.raises(marshmallow.ValidationError):
            schema.lti_user()

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
    def pyramid_request(self, pyramid_request):
        pyramid_request.content_type = "application/x-www-form-urlencoded"
        return pyramid_request

    @pytest.fixture
    def schema(self, pyramid_request):
        return LTI11AuthSchema(pyramid_request)


class TestLTI13AuthSchema:
    def test_lti_user(
        self, schema, schema_params, LTIUser, application_instance_service
    ):
        lti_user = schema.lti_user()

        LTIUser.from_auth_params.assert_called_once_with(
            application_instance_service.get_by_deployment_id.return_value,
            schema_params,
        )
        assert lti_user == LTIUser.from_auth_params.return_value

    def test_it_raises_missing_application_instance(
        self, schema, application_instance_service
    ):
        application_instance_service.get_by_deployment_id.side_effect = (
            ApplicationInstanceNotFound
        )

        with pytest.raises(ValidationError):
            schema.lti_user()

    def test_it_missing_lti_jwt(self, pyramid_request):
        pyramid_request.lti_jwt = {}

        with pytest.raises(ValidationError) as err_info:
            LTI13AuthSchema(pyramid_request).parse()

        assert set(["deployment_id", "iss", "aud"]) == set(
            err_info.value.messages["form"].keys()
        )

    @pytest.fixture
    def schema(self, pyramid_request):
        return LTI13AuthSchema(pyramid_request)

    @pytest.fixture
    def schema_params(self, schema):
        return schema.parse()

    @pytest.fixture
    def pyramid_request(self, pyramid_request, lti_v13_params):
        pyramid_request.params["id_token"] = sentinel.id_token
        pyramid_request.lti_jwt = lti_v13_params

        return pyramid_request


@pytest.fixture
def LTIUser(patch):
    return patch("lms.validation.authentication._lti.LTIUser")
