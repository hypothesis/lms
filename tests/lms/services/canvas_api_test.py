import datetime
from unittest import mock

import pytest
from requests import ConnectionError
from requests import HTTPError
from requests import ReadTimeout
from requests import Response
from requests import TooManyRedirects

from lms.models import ApplicationInstance, OAuth2Token
from lms.services import CanvasAPIAccessTokenError, CanvasAPIServerError
from lms.services.canvas_api import CanvasAPIClient
from lms.validation import ValidationError


class TestGetToken:
    """Unit tests for CanvasAPIClient.get_token()."""

    def test_it_sends_an_access_token_request(
        self,
        ai_getter,
        access_token_request,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        CanvasAccessTokenResponseSchema,
        pyramid_request,
    ):
        canvas_api_client.get_token("test_authorization_code")

        # It initializes canvas_api_helper correctly.
        CanvasAPIHelper.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key,
            ai_getter,
            pyramid_request.route_url,
        )

        # It gets the access token request from canvas_api_helper.
        canvas_api_helper.access_token_request.assert_called_once_with(
            "test_authorization_code"
        )

        # It sends the access token request.
        canvas_api_helper.validated_response.assert_called_once_with(
            access_token_request, CanvasAccessTokenResponseSchema
        )

    def test_it_returns_the_token_tuple(self, canvas_api_client):
        token = canvas_api_client.get_token("test_authorization_code")

        assert token == ("test_access_token", "test_refresh_token", 3600)

    def test_when_the_response_from_Canvas_omits_optional_parameters(
        self, canvas_api_client, access_token_response
    ):
        # refresh_token and expires_in are optional in OAuth 2.0, so we should
        # be able to handle them being missing from the Canvas API's response.
        del access_token_response.parsed_params["refresh_token"]
        del access_token_response.parsed_params["expires_in"]

        token = canvas_api_client.get_token("test_authorization_code")

        assert token == ("test_access_token", None, None)

    def test_it_raises_CanvasAPIServerError_if_it_receives_an_error_response(
        self, canvas_api_client, canvas_api_helper
    ):
        canvas_api_helper.validated_response.side_effect = CanvasAPIServerError(
            "Test error message"
        )

        with pytest.raises(
            CanvasAPIServerError, match="Test error message"
        ) as exc_info:
            canvas_api_client.get_token("test_authorization_code")

    @pytest.fixture
    def access_token_request(self, canvas_api_helper):
        return canvas_api_helper.access_token_request.return_value

    @pytest.fixture(autouse=True)
    def access_token_response(self, canvas_api_helper):
        access_token_response = canvas_api_helper.validated_response.return_value
        access_token_response.parsed_params = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        return access_token_response

    @pytest.fixture
    def CanvasAccessTokenResponseSchema(self, patch):
        return patch("lms.services.canvas_api.CanvasAccessTokenResponseSchema")


class TestSaveToken:
    """Unit tests for CanvasAPIClient.save_token()."""

    def test_it_updates_an_existing_token_in_the_db(
        self, before, canvas_api_client, db_session, pyramid_request
    ):
        existing_token = OAuth2Token(
            user_id=pyramid_request.lti_user.user_id,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            access_token="old_access_token",
        )
        db_session.add(existing_token)

        canvas_api_client.save_token("new_access_token", "new_refresh_token", 3600)

        assert (
            existing_token.consumer_key == pyramid_request.lti_user.oauth_consumer_key
        )
        assert existing_token.user_id == pyramid_request.lti_user.user_id
        assert existing_token.access_token == "new_access_token"
        assert existing_token.refresh_token == "new_refresh_token"
        assert existing_token.expires_in == 3600
        assert existing_token.received_at >= before

    def test_it_adds_a_new_token_to_the_db_if_none_exists(
        self, before, canvas_api_client, db_session, pyramid_request
    ):
        canvas_api_client.save_token("new_access_token", "new_refresh_token", 3600)

        token = db_session.query(OAuth2Token).one()
        assert token.consumer_key == pyramid_request.lti_user.oauth_consumer_key
        assert token.user_id == pyramid_request.lti_user.user_id
        assert token.access_token == "new_access_token"
        assert token.refresh_token == "new_refresh_token"
        assert token.expires_in == 3600
        assert token.received_at >= before

    @pytest.fixture
    def before(self):
        """A time before the test method was called."""
        return datetime.datetime.utcnow()


class TestListFiles:
    """Unit tests for CanvasAPIClient.list_files()."""

    @pytest.mark.usefixtures("access_token")
    def test_it_sends_a_list_files_request_to_canvas(
        self,
        ai_getter,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        CanvasListFilesResponseSchema,
        pyramid_request,
    ):
        canvas_api_client.list_files("test_course_id")

        # It initializes canvas_api_helper correctly.
        CanvasAPIHelper.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key,
            ai_getter,
            pyramid_request.route_url,
        )

        # It gets the PreparedRequest from the helper.
        canvas_api_helper.list_files_request.assert_called_once_with(
            "test_access_token", "test_course_id"
        )

        prepared_request = canvas_api_helper.list_files_request.return_value

        # It uses the helper to send the PreparedRequest.
        canvas_api_helper.validated_response.assert_called_once_with(
            prepared_request, CanvasListFilesResponseSchema
        )

    @pytest.mark.usefixtures("access_token")
    def test_it_returns_the_list_of_files(self, canvas_api_client, canvas_api_helper):
        files = canvas_api_client.list_files("test_course_id")

        validated_response = canvas_api_helper.validated_response.return_value

        assert files == validated_response.parsed_params

    def test_it_raises_CanvasAPIAccessTokenError_if_we_dont_have_an_access_token(
        self, canvas_api_client
    ):
        with pytest.raises(
            CanvasAPIAccessTokenError,
            match="We don't have a Canvas API access token for this user",
        ):
            canvas_api_client.list_files("test_course_id")

    @pytest.mark.usefixtures("access_token")
    def test_it_raises_CanvasAPIServerError_if_the_request_fails(
        self, canvas_api_client, canvas_api_helper
    ):
        canvas_api_helper.validated_response.side_effect = CanvasAPIServerError(
            "test_error_message"
        )

        with pytest.raises(CanvasAPIServerError, match="test_error_message"):
            canvas_api_client.list_files("test_course_id")


class TestPublicURL:
    """Unit tests for CanvasAPIClient.public_url()."""

    @pytest.mark.usefixtures("access_token")
    def test_it_sends_a_public_url_request_to_canvas(
        self,
        ai_getter,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        CanvasPublicURLResponseSchema,
        pyramid_request,
    ):
        canvas_api_client.public_url("test_file_id")

        # It initializes canvas_api_helper correctly.
        CanvasAPIHelper.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key,
            ai_getter,
            pyramid_request.route_url,
        )

        # It gets the PreparedRequest from the helper.
        canvas_api_helper.public_url_request.assert_called_once_with(
            "test_access_token", "test_file_id"
        )

        prepared_request = canvas_api_helper.public_url_request.return_value

        # It uses the helper to send the PreparedRequest.
        canvas_api_helper.validated_response.assert_called_once_with(
            prepared_request, CanvasPublicURLResponseSchema
        )

    @pytest.mark.usefixtures("access_token")
    def test_it_returns_the_public_url(self, canvas_api_client, canvas_api_helper):
        canvas_api_helper.validated_response.return_value.parsed_params = {
            "public_url": "test_public_url"
        }

        url = canvas_api_client.public_url("test_file_id")

        assert url == "test_public_url"

    def test_it_raises_CanvasAPIAccessTokenError_if_we_dont_have_an_access_token(
        self, canvas_api_client
    ):
        with pytest.raises(
            CanvasAPIAccessTokenError,
            match="We don't have a Canvas API access token for this user",
        ):
            canvas_api_client.public_url("test_file_id")

    @pytest.mark.usefixtures("access_token")
    def test_it_raises_CanvasAPIServerError_if_the_request_fails(
        self, canvas_api_client, canvas_api_helper
    ):
        canvas_api_helper.validated_response.side_effect = CanvasAPIServerError(
            "test_error_message"
        )

        with pytest.raises(CanvasAPIServerError, match="test_error_message"):
            canvas_api_client.public_url("test_file_id")


@pytest.fixture(autouse=True)
def application_instance(db_session, pyramid_request):
    """The ApplicationInstance that the test OAuth2Token's belong to."""
    application_instance = ApplicationInstance(
        consumer_key=pyramid_request.lti_user.oauth_consumer_key,
        shared_secret="test_shared_secret",
        lms_url="test_lms_url",
        requesters_email="test_requesters_email",
    )
    db_session.add(application_instance)
    return application_instance


@pytest.fixture
def access_token(db_session, pyramid_request):
    access_token = OAuth2Token(
        user_id=pyramid_request.lti_user.user_id,
        consumer_key=pyramid_request.lti_user.oauth_consumer_key,
        access_token="test_access_token",
    )
    db_session.add(access_token)
    return access_token


@pytest.fixture
def CanvasAccessTokenResponseSchema(patch):
    return patch("lms.services.canvas_api.CanvasAccessTokenResponseSchema")


@pytest.fixture
def CanvasListFilesResponseSchema(patch):
    return patch("lms.services.canvas_api.CanvasListFilesResponseSchema")


@pytest.fixture
def CanvasPublicURLResponseSchema(patch):
    return patch("lms.services.canvas_api.CanvasPublicURLResponseSchema")


@pytest.fixture
def canvas_api_client(pyramid_config, pyramid_request):
    return CanvasAPIClient(mock.sentinel.context, pyramid_request)


@pytest.fixture(autouse=True)
def CanvasAPIHelper(patch):
    return patch("lms.services.canvas_api.CanvasAPIHelper")


@pytest.fixture
def canvas_api_helper(CanvasAPIHelper):
    return CanvasAPIHelper.return_value
