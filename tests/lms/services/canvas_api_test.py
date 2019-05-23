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

    @pytest.mark.usefixtures("access_token_response")
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

    @pytest.mark.usefixtures("access_token", "list_files_response")
    def test_list_files_sends_a_list_files_request_to_canvas(
        self,
        ai_getter,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        list_files_request,
        pyramid_request,
        requests,
    ):
        canvas_api_client.list_files("test_course_id")

        # It initializes canvas_api_helper correctly.
        CanvasAPIHelper.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key,
            ai_getter,
            pyramid_request.route_url,
        )

        # It gets the list files request from canvas_api_helper.
        canvas_api_helper.list_files_request.assert_called_once_with(
            "test_access_token", "test_course_id"
        )

        # It sends the list files request.
        requests.Session.assert_called_once_with()
        requests.Session.return_value.send.assert_called_once_with(list_files_request)

    @pytest.mark.usefixtures("access_token", "list_files_response")
    def test_list_files_returns_the_list_of_files(self, canvas_api_client):
        files = canvas_api_client.list_files("test_course_id")

        assert files == [
            {
                "display_name": "TEST FILE 1",
                "id": 188,
                "updated_at": "2019-05-08T15:22:31Z",
            },
            {
                "display_name": "TEST FILE 2",
                "id": 181,
                "updated_at": "2019-02-14T00:33:01Z",
            },
            {
                "display_name": "TEST FILE 3",
                "id": 97,
                "updated_at": "2018-10-19T17:16:50Z",
            },
        ]

    @pytest.mark.usefixtures("access_token", "public_url_response")
    def test_public_url_sends_a_public_url_request_to_canvas(
        self,
        ai_getter,
        canvas_api_client,
        CanvasAPIHelper,
        canvas_api_helper,
        public_url_request,
        pyramid_request,
        requests,
    ):
        canvas_api_client.public_url("test_file_id")

        # It initializes canvas_api_helper correctly.
        CanvasAPIHelper.assert_called_once_with(
            pyramid_request.lti_user.oauth_consumer_key,
            ai_getter,
            pyramid_request.route_url,
        )

        # It gets the public URL request from canvas_api_helper.
        canvas_api_helper.public_url_request.assert_called_once_with(
            "test_access_token", "test_file_id"
        )

        # It sends the public URL request.
        requests.Session.assert_called_once_with()
        requests.Session.return_value.send.assert_called_once_with(public_url_request)

    @pytest.mark.usefixtures("access_token", "public_url_response")
    def test_public_url_returns_the_public_url(self, canvas_api_client):
        assert (
            canvas_api_client.public_url("test_file_id")
            == "https://example-bucket.s3.amazonaws.com/example-namespace/attachments/1/example-filename?AWSAccessKeyId=example-key&Expires=1400000000&Signature=example-signature"
        )

    @pytest.fixture
    def access_token(self, db_session, pyramid_request):
        access_token = OAuth2Token(
            user_id=pyramid_request.lti_user.user_id,
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            access_token="test_access_token",
        )
        db_session.add(access_token)
        return access_token

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
    def access_token_response(self, requests):
        """Configure requests to send back access token responses."""
        access_token_response = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
        }
        requests.Session.return_value.send.return_value.json.return_value = (
            access_token_response
        )
        return access_token_response

    @pytest.fixture
    def list_files_response(self, requests):
        """Configure requests to send back Canvas list files API responses."""
        list_files_response = [
            {
                "content-type": "application/pdf",
                "created_at": "2018-11-22T08:46:38Z",
                "display_name": "TEST FILE 1",
                "filename": "TEST_FILE_1.pdf",
                "folder_id": 81,
                "hidden": False,
                "hidden_for_user": False,
                "id": 188,
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "pdf",
                "modified_at": "2018-11-22T08:46:38Z",
                "size": 2435546,
                "thumbnail_url": None,
                "unlock_at": None,
                "updated_at": "2019-05-08T15:22:31Z",
                "upload_status": "success",
                "url": "TEST_URL_1",
                "uuid": "TEST_UUID_1",
                "workflow_state": "processing",
            },
            {
                "content-type": "application/pdf",
                "created_at": "2018-10-25T15:04:08Z",
                "display_name": "TEST FILE 2",
                "filename": "TEST_FILE_2.pdf",
                "folder_id": 17,
                "hidden": False,
                "hidden_for_user": False,
                "id": 181,
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "pdf",
                "modified_at": "2018-10-25T15:04:08Z",
                "size": 1407214,
                "thumbnail_url": None,
                "unlock_at": None,
                "updated_at": "2019-02-14T00:33:01Z",
                "upload_status": "success",
                "url": "TEST_URL_2",
                "uuid": "TEST_UUID_2",
                "workflow_state": "processing",
            },
            {
                "content-type": "application/pdf",
                "created_at": "2017-09-08T11:05:03Z",
                "display_name": "TEST FILE 3",
                "filename": "TEST_FILE_3.pdf",
                "folder_id": 17,
                "hidden": False,
                "hidden_for_user": False,
                "id": 97,
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "pdf",
                "modified_at": "2017-09-08T11:05:03Z",
                "size": 265615,
                "thumbnail_url": None,
                "unlock_at": None,
                "updated_at": "2018-10-19T17:16:50Z",
                "upload_status": "success",
                "url": "TEST_URL_3",
                "uuid": "TEST_UUID_3",
                "workflow_state": "processing",
            },
        ]
        requests.Session.return_value.send.return_value.json.return_value = (
            list_files_response
        )
        return list_files_response

    @pytest.fixture
    def public_url_response(self, requests):
        """Configure requests to send back public URL responses."""
        public_url_response = {
            "public_url": "https://example-bucket.s3.amazonaws.com/example-namespace/attachments/1/example-filename?AWSAccessKeyId=example-key&Expires=1400000000&Signature=example-signature"
        }
        requests.Session.return_value.send.return_value.json.return_value = (
            public_url_response
        )
        return public_url_response

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


@pytest.fixture
def list_files_request(canvas_api_helper):
    return canvas_api_helper.list_files_request.return_value


@pytest.fixture
def public_url_request(canvas_api_helper):
    return canvas_api_helper.public_url_request.return_value


@pytest.fixture(autouse=True)
def requests(patch):
    requests = patch("lms.services.canvas_api.requests")
    requests.Session.return_value.send.return_value = mock.create_autospec(
        _requests.Response, instance=True, spec_set=True
    )
    return requests
