from unittest.mock import sentinel

import pytest

from lms.services import BlackboardFileNotFoundInCourse, HTTPError
from lms.services.blackboard_api.service import BlackboardAPIClient, factory
from lms.validation import ValidationError
from tests import factories


class TestBlackboardAPIClient:
    def test_get_token(
        self,
        svc,
        http_service,
        oauth2_token_service,
        OAuthTokenResponseSchema,
        oauth_token_response_schema,
    ):
        oauth_token_response_schema.parse.return_value = {
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
        )

        # It validates the response.
        OAuthTokenResponseSchema.assert_called_once_with(http_service.post.return_value)

        # It saves the access token in the DB.
        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, sentinel.refresh_token, sentinel.expires_in
        )

    def test_get_token_raises_HTTPError_if_the_HTTP_request_fails(
        self, svc, http_service
    ):
        http_service.post.side_effect = HTTPError

        with pytest.raises(HTTPError):
            svc.get_token(sentinel.authorization_code)

    def test_get_token_raises_ValidationError_if_Blackboards_response_is_invalid(
        self, svc, oauth_token_response_schema
    ):
        oauth_token_response_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            svc.get_token(sentinel.authorization_code)

    def test_get_token_if_theres_no_refresh_token_or_expires_in(
        self, svc, oauth2_token_service, oauth_token_response_schema
    ):
        # refresh_token and expires_in are optional fields in
        # OAuthTokenResponseSchema so get_token() has to still work if they're
        # missing from the validated data.
        oauth_token_response_schema.parse.return_value = {
            "access_token": sentinel.access_token
        }

        svc.get_token(sentinel.authorization_code)

        oauth2_token_service.save.assert_called_once_with(
            sentinel.access_token, None, None
        )

    def test_list_files(
        self, svc, http_service, BlackboardListFilesSchema, blackboard_list_files_schema
    ):
        files = svc.list_files("TEST_COURSE_ID")

        http_service.get.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/courses/uuid:TEST_COURSE_ID/resources",
            oauth=True,
        )
        BlackboardListFilesSchema.assert_called_once_with(http_service.get.return_value)
        assert files == blackboard_list_files_schema.parse.return_value

    def test_list_files_raises_HTTPError_if_the_HTTP_request_fails(
        self, svc, http_service
    ):
        http_service.get.side_effect = HTTPError

        with pytest.raises(HTTPError):
            svc.list_files("TEST_COURSE_ID")

    def test_list_files_raises_ValidationError_if_Blackboards_response_is_invalid(
        self, svc, blackboard_list_files_schema
    ):
        blackboard_list_files_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            svc.list_files("TEST_COURSE_ID")

    def test_public_url(
        self, svc, http_service, BlackboardPublicURLSchema, blackboard_public_url_schema
    ):
        public_url = svc.public_url(
            "TEST_COURSE_ID", "blackboard://content-resource/TEST_FILE_ID/"
        )

        http_service.get.assert_called_once_with(
            "https://blackboard.example.com/learn/api/public/v1/courses/uuid:TEST_COURSE_ID/resources/TEST_FILE_ID",
            oauth=True,
        )
        BlackboardPublicURLSchema.assert_called_once_with(http_service.get.return_value)
        assert public_url == blackboard_public_url_schema.parse.return_value

    def test_public_url_raises_HTTPError_if_the_HTTP_request_fails(
        self, svc, http_service
    ):
        http_service.get.side_effect = HTTPError(
            factories.requests.Response(status_code=400)
        )

        with pytest.raises(HTTPError):
            svc.public_url(
                "TEST_COURSE_ID", "blackboard://content-resource/TEST_FILE_ID/"
            )

    def test_public_url_raises_BlackboardFileNotFoundInCourse_if_the_file_isnt__in_the_course(
        self, svc, http_service
    ):
        response = factories.requests.Response(status_code=404)
        http_service.get.side_effect = HTTPError(response)

        with pytest.raises(BlackboardFileNotFoundInCourse):
            svc.public_url(
                "TEST_COURSE_ID", "blackboard://content-resource/TEST_FILE_ID/"
            )

    def test_public_url_raises_ValidationError_if_Blackboards_response_is_invalid(
        self, svc, blackboard_public_url_schema
    ):
        blackboard_public_url_schema.parse.side_effect = ValidationError({})

        with pytest.raises(ValidationError):
            svc.public_url(
                "TEST_COURSE_ID", "blackboard://content-resource/TEST_FILE_ID/"
            )

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


@pytest.fixture(autouse=True)
def BlackboardListFilesSchema(patch):
    return patch("lms.services.blackboard_api.service.BlackboardListFilesSchema")


@pytest.fixture
def blackboard_list_files_schema(BlackboardListFilesSchema):
    return BlackboardListFilesSchema.return_value


@pytest.fixture(autouse=True)
def BlackboardPublicURLSchema(patch):
    return patch("lms.services.blackboard_api.service.BlackboardPublicURLSchema")


@pytest.fixture
def blackboard_public_url_schema(BlackboardPublicURLSchema):
    return BlackboardPublicURLSchema.return_value


@pytest.fixture(autouse=True)
def OAuthTokenResponseSchema(patch):
    return patch("lms.services.blackboard_api.service.OAuthTokenResponseSchema")


@pytest.fixture
def oauth_token_response_schema(OAuthTokenResponseSchema):
    return OAuthTokenResponseSchema.return_value
