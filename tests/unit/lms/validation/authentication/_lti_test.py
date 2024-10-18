from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.models import LTIParams
from lms.services import ApplicationInstanceNotFound, LTILaunchVerificationError
from lms.validation._exceptions import ValidationError
from lms.validation.authentication import LTI11AuthSchema, LTI13AuthSchema

pytestmark = pytest.mark.usefixtures(
    "launch_verifier", "application_instance_service", "lti_user_service"
)


class TestLTI11AuthSchema:
    def test_it_returns_the_lti_user_info(
        self, schema, application_instance_service, lti_user_service, pyramid_request
    ):
        lti_user = schema.lti_user()

        lti_user_service.from_lti_params.assert_called_once_with(
            application_instance_service.get_by_consumer_key.return_value,
            pyramid_request.lti_params,
        )
        assert lti_user == lti_user_service.from_lti_params.return_value

    def test_it_raises_missing_application_instance(
        self, schema, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        with pytest.raises(ValidationError):
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
        self, schema, pyramid_request, application_instance_service, lti_user_service
    ):
        lti_user = schema.lti_user()

        lti_user_service.from_lti_params.assert_called_once_with(
            application_instance_service.get_by_deployment_id.return_value,
            pyramid_request.lti_params,
        )
        assert lti_user == lti_user_service.from_lti_params.return_value

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

        assert {"deployment_id", "iss", "aud"} == set(
            err_info.value.messages["form"].keys()
        )

    @pytest.fixture
    def schema(self, pyramid_request):
        return LTI13AuthSchema(pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request, lti_v13_params):
        pyramid_request.params["id_token"] = sentinel.id_token
        pyramid_request.lti_jwt = lti_v13_params
        pyramid_request.lti_params = LTIParams.from_request(pyramid_request)

        return pyramid_request
