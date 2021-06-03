from unittest.mock import sentinel

import pytest

from lms.services import HTTPError, HTTPValidationError
from lms.services.blackboard_api._schemas import BlackboardListFilesSchema
from lms.services.blackboard_api.service import BlackboardAPIClient, factory
from lms.validation.authentication import OAuthTokenResponseSchema


class TestBlackboardAPIClient:
    def test_get_token(self, svc, http_service, oauth2_token_service):
        http_service.post.return_value.validated_data = {
            "access_token": sentinel.access_token,
            "refresh_token": sentinel.refresh_token,
            "expires_in": sentinel.expires_in,
        }

        svc.get_token(sentinel.authorization_code)

        # It calls the Blackboard API to get the access token.
        http_service.post.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": sentinel.redirect_uri,
                "code": sentinel.authorization_code,
            },
            auth=(sentinel.client_id, sentinel.client_secret),
            schema=OAuthTokenResponseSchema,
        )

        # It saves the access token in the DB.
        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, sentinel.refresh_token, sentinel.expires_in
        )

    @pytest.mark.parametrize("exception_class", [HTTPError, HTTPValidationError])
    def test_get_token_raises_if_HTTPService_raises(
        self, svc, http_service, exception_class
    ):
        http_service.post.side_effect = exception_class

        with pytest.raises(exception_class):
            svc.get_token(sentinel.authorization_code)

    def test_get_token_if_theres_no_refresh_token_or_expires_in(
        self, svc, http_service, oauth2_token_service
    ):
        # refresh_token and expires_in are optional fields in
        # OAuthTokenResponseSchema so get_token() has to still work if they're
        # missing from the validated data.
        http_service.post.return_value.validated_data = {
            "access_token": sentinel.access_token
        }

        svc.get_token(sentinel.authorization_code)

        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, None, None
        )

    def test_list_files(self, svc, http_service):
        files = svc.list_files("TEST_COURSE_ID")

        http_service.get.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/courses/uuid:TEST_COURSE_ID/resources",
            oauth=True,
            schema=BlackboardListFilesSchema,
        )
        assert files == http_service.get.return_value.validated_data

    @pytest.mark.parametrize("exception_class", [HTTPError, HTTPValidationError])
    def test_list_files_raises_if_HTTPService_raises(
        self, svc, http_service, exception_class
    ):
        http_service.get.side_effect = exception_class

        with pytest.raises(exception_class):
            svc.list_files(sentinel.course_id)

    @pytest.fixture
    def svc(self, http_service, oauth2_token_service):
        return BlackboardAPIClient(
            blackboard_host="blackboard.example.com",
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
            http_service=http_service,
            oauth2_token_service=oauth2_token_service,
        )


@pytest.mark.usefixtures(
    "application_instance_service", "http_service", "oauth2_token_service"
)
class TestFactory:
    def test_it(
        self,
        application_instance_service,
        http_service,
        oauth2_token_service,
        pyramid_request,
        BlackboardAPIClient,
    ):
        application_instance = application_instance_service.get.return_value
        settings = pyramid_request.registry.settings

        service = factory(sentinel.context, pyramid_request)

        BlackboardAPIClient.assert_called_once_with(
            blackboard_host=application_instance.lms_host(),
            client_id=settings["blackboard_api_client_id"],
            client_secret=settings["blackboard_api_client_secret"],
            redirect_uri=pyramid_request.route_url("blackboard_api.oauth.callback"),
            http_service=http_service,
            oauth2_token_service=oauth2_token_service,
        )
        assert service == BlackboardAPIClient.return_value

    @pytest.fixture(autouse=True)
    def BlackboardAPIClient(self, patch):
        return patch("lms.services.blackboard_api.service.BlackboardAPIClient")
