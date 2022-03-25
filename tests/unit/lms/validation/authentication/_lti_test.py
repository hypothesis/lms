from unittest.mock import sentinel

import pytest

from lms.services import ApplicationInstanceNotFound
from lms.validation._exceptions import ValidationError
from lms.validation.authentication import LTI13AuthSchema

pytestmark = pytest.mark.usefixtures("application_instance_service")


class TestLaunchParamsAuthSchema:
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
    def LTIUser(self, patch):
        return patch("lms.validation.authentication._lti.LTIUser")
