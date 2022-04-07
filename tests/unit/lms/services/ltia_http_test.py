from datetime import datetime
from unittest.mock import sentinel

import pytest
from freezegun import freeze_time

from lms.services.ltia_http import LTIAHTTPService, factory
from tests import factories


class TestLTIAHTTPService:
    @freeze_time("2022-04-04")
    def test_request(self, svc, jwt_service, application_instance, uuid, http_service):
        response = svc.request(["SCOPE_1", "SCOPE_2"], "POST", "https://example.com")

        jwt_service.encode_with_private_key.assert_called_once_with(
            {
                "aud": application_instance.lti_registration.token_url,
                "exp": datetime(2022, 4, 4, 1, 0),
                "iat": datetime(2022, 4, 4, 0, 0),
                "nonce": uuid.uuid4.return_value.hex,
                "iss": application_instance.lti_registration.client_id,
                "sub": application_instance.lti_registration.client_id,
                "jti": uuid.uuid4.return_value.hex,
            }
        )
        http_service.post.assert_called_once_with(
            application_instance.lti_registration.token_url,
            data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": jwt_service.encode_with_private_key.return_value,
                "scope": "SCOPE_1 SCOPE_2",
            },
        )
        http_service.request.assert_called_once_with(
            "POST",
            "https://example.com",
            headers={
                "Authorization": f"Bearer {http_service.post.return_value.json.return_value['access_token']}"
            },
        )
        assert response == http_service.request.return_value

    @pytest.fixture
    def svc(self, application_instance, jwt_service, http_service):
        return LTIAHTTPService(
            application_instance.lti_registration, jwt_service, http_service
        )

    @pytest.fixture
    def uuid(self, patch):
        return patch("lms.services.ltia_http.uuid")


class TestFactory:
    @pytest.mark.usefixtures("application_instance_service")
    def test_it(
        self,
        pyramid_request,
        LTIAHTTPService,
        application_instance,
        http_service,
        jwt_service,
    ):
        ltia_http_service = factory(sentinel.context, pyramid_request)

        LTIAHTTPService.assert_called_once_with(
            application_instance.lti_registration, jwt_service, http_service
        )
        assert ltia_http_service == LTIAHTTPService.return_value

    @pytest.fixture
    def LTIAHTTPService(self, patch):
        return patch("lms.services.ltia_http.LTIAHTTPService")


@pytest.mark.usefixtures("db_session")
@pytest.fixture
def application_instance(application_instance):
    application_instance.lti_registration = factories.LTIRegistration()
    return application_instance
