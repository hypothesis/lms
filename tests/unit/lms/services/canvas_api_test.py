from unittest import mock

import pytest

from lms.models import ApplicationInstance, OAuth2Token
from lms.services import CanvasAPIAccessTokenError, CanvasAPIServerError
from lms.services.canvas_api import CanvasAPIClient


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

    def test_it_saves_the_access_token_to_the_db(self, canvas_api_client, db_session):
        canvas_api_client.get_token("test_authorization_code")

        oauth2_token = db_session.query(OAuth2Token).one()
        assert oauth2_token.user_id == "TEST_USER_ID"
        assert oauth2_token.consumer_key == "TEST_OAUTH_CONSUMER_KEY"
        assert oauth2_token.access_token == "test_access_token"
        assert oauth2_token.refresh_token == "test_refresh_token"
        assert oauth2_token.expires_in == 3600

    def test_when_the_response_from_Canvas_omits_optional_parameters(
        self, canvas_api_client, access_token_response, db_session
    ):
        # refresh_token and expires_in are optional in OAuth 2.0, so we should
        # be able to handle them being missing from the Canvas API's response.
        del access_token_response.parsed_params["refresh_token"]
        del access_token_response.parsed_params["expires_in"]

        canvas_api_client.get_token("test_authorization_code")

        oauth2_token = db_session.query(OAuth2Token).one()
        assert oauth2_token.user_id == "TEST_USER_ID"
        assert oauth2_token.consumer_key == "TEST_OAUTH_CONSUMER_KEY"
        assert oauth2_token.access_token == "test_access_token"
        assert oauth2_token.refresh_token is None
        assert oauth2_token.expires_in is None

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


class TestGetRefreshedToken:
    """Unit tests for CanvasAPIClient.get_refreshed_token()."""

    def test_it_sends_a_refresh_token_request(
        self,
        ai_getter,
        refresh_token_request,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        CanvasRefreshTokenResponseSchema,
        pyramid_request,
    ):
        canvas_api_client.get_refreshed_token("test_refresh_token")

        # It initializes canvas_api_helper correctly.
        CanvasAPIHelper.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key,
            ai_getter,
            pyramid_request.route_url,
        )

        # It gets the refresh token request from canvas_api_helper.
        canvas_api_helper.refresh_token_request.assert_called_once_with(
            "test_refresh_token"
        )

        # It sends the refresh token request.
        canvas_api_helper.validated_response.assert_called_once_with(
            refresh_token_request, CanvasRefreshTokenResponseSchema
        )

    def test_it_saves_the_new_access_token_to_the_db(
        self, canvas_api_client, db_session
    ):
        canvas_api_client.get_refreshed_token("test_refresh_token")

        oauth2_token = db_session.query(OAuth2Token).one()
        assert oauth2_token.user_id == "TEST_USER_ID"
        assert oauth2_token.consumer_key == "TEST_OAUTH_CONSUMER_KEY"
        assert oauth2_token.access_token == "new_access_token"
        assert oauth2_token.refresh_token == "new_refresh_token"
        assert oauth2_token.expires_in == 6400

    def test_it_returns_the_new_access_token(self, canvas_api_client):
        new_access_token = canvas_api_client.get_refreshed_token("test_refresh_token")

        assert new_access_token == "new_access_token"

    def test_when_the_response_from_Canvas_omits_optional_parameters(
        self, canvas_api_client, refresh_token_response, db_session
    ):
        # refresh_token and expires_in are optional in OAuth 2.0, so we should
        # be able to handle them being missing from the Canvas API's response.
        del refresh_token_response.parsed_params["refresh_token"]
        del refresh_token_response.parsed_params["expires_in"]

        canvas_api_client.get_refreshed_token("old_refresh_token")

        oauth2_token = db_session.query(OAuth2Token).one()
        assert oauth2_token.user_id == "TEST_USER_ID"
        assert oauth2_token.consumer_key == "TEST_OAUTH_CONSUMER_KEY"
        assert oauth2_token.access_token == "new_access_token"
        assert oauth2_token.refresh_token == "old_refresh_token"
        assert oauth2_token.expires_in is None

    def test_it_raises_CanvasAPIServerError_if_it_receives_an_error_response(
        self, canvas_api_client, canvas_api_helper
    ):
        canvas_api_helper.validated_response.side_effect = CanvasAPIServerError(
            "Test error message"
        )

        with pytest.raises(
            CanvasAPIServerError, match="Test error message"
        ) as exc_info:
            canvas_api_client.get_refreshed_token("test_refresh_token")

    @pytest.fixture
    def refresh_token_request(self, canvas_api_helper):
        return canvas_api_helper.refresh_token_request.return_value

    @pytest.fixture(autouse=True)
    def refresh_token_response(self, canvas_api_helper):
        refresh_token_response = canvas_api_helper.validated_response.return_value
        refresh_token_response.parsed_params = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 6400,
        }
        return refresh_token_response

    @pytest.fixture
    def CanvasRefreshTokenResponseSchema(self, patch):
        return patch("lms.services.canvas_api.CanvasRefreshTokenResponseSchema")

    @pytest.fixture(autouse=True)
    def old_oauth2_token(self, db_session, pyramid_request):
        old_oauth2_token = OAuth2Token(
            user_id=pyramid_request.lti_user.user_id,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            access_token="old_access_token",
            refresh_token="old_refresh_token",
            expires_in=3600,
        )
        db_session.add(old_oauth2_token)
        return old_oauth2_token


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


class TestSendWithRefreshAndRetry:
    def test_it_sends_the_request_and_returns_the_parsed_params(
        self,
        canvas_api_client,
        canvas_api_helper,
        prepared_request,
        Schema,
        refresh_token,
    ):
        parsed_params = canvas_api_client.send_with_refresh_and_retry(
            prepared_request, Schema, refresh_token
        )

        canvas_api_helper.validated_response.assert_called_once_with(
            prepared_request, Schema
        )
        assert (
            parsed_params
            == canvas_api_helper.validated_response.return_value.parsed_params
        )

    def test_if_the_request_raises_CanvasAPIServerError_it_raises(
        self,
        canvas_api_client,
        canvas_api_helper,
        prepared_request,
        Schema,
        refresh_token,
    ):
        canvas_api_helper.validated_response.side_effect = CanvasAPIServerError(
            "test_error"
        )

        with pytest.raises(CanvasAPIServerError, match="test_error"):
            canvas_api_client.send_with_refresh_and_retry(
                prepared_request, Schema, refresh_token
            )

    def test_if_the_request_raises_CanvasAPIAccessTokenError_and_theres_no_refresh_token_it_raises(
        self,
        canvas_api_client,
        canvas_api_helper,
        prepared_request,
        Schema,
        refresh_token,
    ):
        canvas_api_helper.validated_response.side_effect = CanvasAPIAccessTokenError(
            "test_error"
        )

        with pytest.raises(CanvasAPIAccessTokenError, match="test_error"):
            canvas_api_client.send_with_refresh_and_retry(
                prepared_request, Schema, refresh_token=None
            )

    def test_if_the_request_raises_CanvasAPIAccessTokenError_it_refreshes_and_retries(
        self,
        canvas_api_client,
        canvas_api_helper,
        prepared_request,
        Schema,
        refresh_token,
        get_refreshed_token,
    ):
        # Make validated_response() raise only the first time it's called.
        canvas_api_helper.validated_response.side_effect = [
            CanvasAPIAccessTokenError("test_error"),
            mock.DEFAULT,
        ]

        parsed_params = canvas_api_client.send_with_refresh_and_retry(
            prepared_request, Schema, refresh_token
        )

        get_refreshed_token.assert_called_once_with(canvas_api_client, refresh_token)
        assert canvas_api_helper.validated_response.call_args_list == [
            mock.call(prepared_request, Schema),
            mock.call(prepared_request, Schema, get_refreshed_token.return_value),
        ]
        assert (
            parsed_params
            == canvas_api_helper.validated_response.return_value.parsed_params
        )

    def test_if_the_refresh_request_raises_it_raises(
        self,
        canvas_api_client,
        canvas_api_helper,
        prepared_request,
        Schema,
        refresh_token,
        get_refreshed_token,
    ):
        # Make validated_response() raise only the first time it's called.
        canvas_api_helper.validated_response.side_effect = [
            CanvasAPIAccessTokenError("test_error"),
            mock.DEFAULT,
        ]
        # Make the refresh token request raise.
        get_refreshed_token.side_effect = CanvasAPIServerError("test_error")

        with pytest.raises(CanvasAPIServerError, match="test_error"):
            canvas_api_client.send_with_refresh_and_retry(
                prepared_request, Schema, refresh_token
            )

    def test_if_the_request_raises_the_second_time_it_raises(
        self,
        canvas_api_client,
        canvas_api_helper,
        prepared_request,
        Schema,
        refresh_token,
    ):
        # Make validated_response() raise both times it's called.
        canvas_api_helper.validated_response.side_effect = [
            CanvasAPIAccessTokenError("first_error"),
            CanvasAPIServerError("second_error"),
        ]

        with pytest.raises(CanvasAPIServerError, match="second_error"):
            canvas_api_client.send_with_refresh_and_retry(
                prepared_request, Schema, refresh_token
            )

    @pytest.fixture
    def prepared_request(self):
        """The PreparedRequest that we're sending."""
        return mock.sentinel.request

    @pytest.fixture
    def Schema(self):
        """The schema class we're using to validate the responses."""
        return mock.sentinel.Schema

    @pytest.fixture
    def refresh_token(self):
        """The refresh token we're using if our access token has expired."""
        return mock.sentinel.refresh_token

    @pytest.fixture(autouse=True)
    def get_refreshed_token(self, patch):
        return patch("lms.services.canvas_api.CanvasAPIClient.get_refreshed_token")


pytestmark = pytest.mark.usefixtures("ai_getter")


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
def canvas_api_client(CanvasAPIHelper, pyramid_config, pyramid_request):
    return CanvasAPIClient(mock.sentinel.context, pyramid_request)


@pytest.fixture(autouse=True)
def CanvasAPIHelper(patch):
    return patch("lms.services.canvas_api.CanvasAPIHelper")


@pytest.fixture
def canvas_api_helper(CanvasAPIHelper):
    return CanvasAPIHelper.return_value
