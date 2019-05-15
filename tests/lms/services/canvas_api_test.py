import datetime
from unittest import mock

import pytest
import requests as _requests

from lms.models import ApplicationInstance, OAuth2Token
from lms.services.canvas_api import CanvasAPIClient


class TestCanvasAPIClient:
    def test_get_token_sends_an_access_token_request(
        self,
        ai_getter,
        access_token_request,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        pyramid_request,
        requests,
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
        requests.Session.assert_called_once_with()
        requests.Session.return_value.send.assert_called_once_with(access_token_request)

    def test_get_token_returns_the_token_tuple(self, canvas_api_client):
        token = canvas_api_client.get_token("test_authorization_code")

        assert token == ("test_access_token", "test_refresh_token", 3600)

    def test_save_token_updates_an_existing_token_in_the_db(
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

    def test_save_token_adds_a_new_token_to_the_db_if_none_exists(
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
    def canvas_api_client(self, pyramid_config, pyramid_request):
        return CanvasAPIClient(mock.sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def application_instance(self, db_session, pyramid_request):
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
    def before(self):
        """A time before the test method was called."""
        return datetime.datetime.utcnow()


@pytest.fixture(autouse=True)
def CanvasAPIHelper(patch):
    return patch("lms.services.canvas_api.CanvasAPIHelper")


@pytest.fixture
def canvas_api_helper(CanvasAPIHelper):
    return CanvasAPIHelper.return_value


@pytest.fixture
def access_token_request(canvas_api_helper):
    return canvas_api_helper.access_token_request.return_value


@pytest.fixture(autouse=True)
def requests(patch):
    requests = patch("lms.services.canvas_api.requests")
    requests.Session.return_value.send.return_value = mock.create_autospec(
        _requests.Response, instance=True, spec_set=True
    )
    requests.Session.return_value.send.return_value.json.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
    }
    return requests
