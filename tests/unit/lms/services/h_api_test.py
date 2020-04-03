from unittest.mock import call, patch, sentinel

import pytest
import requests as requests_
from h_matchers import Any
from requests import (
    HTTPError,
    ReadTimeout,
    RequestException,
    Response,
    TooManyRedirects,
)

from lms.services import HAPIError, HAPINotFoundError
from lms.services.h_api import HAPI
from lms.values import HUser


class TestHAPI:

    # We're accessing h_api._api_request a lot in this test class, so disable
    # protected-access messages.
    # pylint: disable=protected-access

    def test_get_user_works(self, h_api, _api_request):
        _api_request.return_value.json.return_value = {
            "display_name": sentinel.display_name
        }

        user = h_api.get_user("username")

        _api_request.assert_called_once_with(
            "GET", path="users/acct:username@TEST_AUTHORITY"
        )

        assert user == Any.instance_of(HUser)
        assert user.authority == "TEST_AUTHORITY"
        assert user.username == "username"
        assert user.display_name == sentinel.display_name

    def test_create_user_works(self, h_api, h_user, _api_request):
        h_api.create_user(h_user, sentinel.provider, sentinel.provider_unique_id)

        _api_request.assert_called_once_with(
            "POST",
            "users",
            data={
                "username": h_user.username,
                "display_name": h_user.display_name,
                "authority": "TEST_AUTHORITY",
                "identities": [
                    {
                        "provider": sentinel.provider,
                        "provider_unique_id": sentinel.provider_unique_id,
                    }
                ],
            },
        )

    def test_update_user_works(self, h_api, h_user, _api_request):
        h_api.update_user(h_user)

        _api_request.assert_called_once_with(
            "PATCH",
            "users/sentinel.username",
            data={"display_name": h_user.display_name},
        )

    def test_upsert_user_calls_create_if_update_fails(
        self, update_user, create_user, h_api, h_user
    ):
        update_user.side_effect = HAPINotFoundError()
        h_api.upsert_user(h_user, sentinel.provider, sentinel.provider_unique_id)

        update_user.assert_called_once_with(h_user)
        create_user.assert_called_once_with(
            h_user, sentinel.provider, sentinel.provider_unique_id
        )

    def test_upsert_group_works(self, h_api, _api_request, upsert_group_call):
        h_api.upsert_group(sentinel.group_id, sentinel.group_name)

        assert _api_request.call_args_list == [upsert_group_call]

    def test_upsert_group_raises_if_creating_the_group_fails(
        self, h_api, _api_request, upsert_group_call
    ):
        # If the first attempt to upsert the group fails with anything other
        # than a 404, upsert_group() raises.
        _api_request.side_effect = HAPIError("test_error_message")

        with pytest.raises(HAPIError, match="test_error_message"):
            h_api.upsert_group(sentinel.group_id, sentinel.group_name)

        assert _api_request.call_args_list == [upsert_group_call]

    def test_upsert_group_creates_the_lms_user_if_it_doesnt_exist(
        self, h_api, _api_request, upsert_group_call, create_user_call
    ):
        # Make only the first h API call (the first attempt to upsert the
        # group) fail.
        _api_request.side_effect = [HAPINotFoundError(), None, None]

        h_api.upsert_group(sentinel.group_id, sentinel.group_name)

        # It should have tried to upsert the group once, then created the user,
        # then tried again to upsert the group.
        assert _api_request.call_args_list == [
            upsert_group_call,
            create_user_call,
            upsert_group_call,
        ]

    def test_upsert_group_raises_if_creating_the_lms_user_fails(
        self, h_api, _api_request, upsert_group_call, create_user_call
    ):
        # Make the first attempt to upsert the group fail because the lms user
        # doesn't exist, and make the attempt to create the lms user also fail.
        _api_request.side_effect = [
            HAPINotFoundError(),
            HAPIError("test_error_message"),
            None,
        ]

        with pytest.raises(HAPIError, match="test_error_message"):
            h_api.upsert_group(sentinel.group_id, sentinel.group_name)

        # It should have tried to upsert the group once then tried to create
        # the user (which failed).
        assert _api_request.call_args_list == [upsert_group_call, create_user_call]

    def test_upsert_group_raises_if_the_second_attempt_to_upsert_the_group_fails(
        self, h_api, _api_request, upsert_group_call, create_user_call
    ):
        # Make both attempts to upsert the group fail, but let creating the lms
        # user succeed.
        _api_request.side_effect = [
            HAPINotFoundError(),
            None,
            HAPIError("test_error_message"),
        ]

        with pytest.raises(HAPIError, match="test_error_message"):
            h_api.upsert_group(sentinel.group_id, sentinel.group_name)

        assert _api_request.call_args_list == [
            upsert_group_call,
            create_user_call,
            upsert_group_call,
        ]

    def test_update_group_works(self, h_api, _api_request):
        h_api.update_group(sentinel.group_id, sentinel.group_name)

        _api_request.assert_called_once_with(
            "PATCH", "groups/sentinel.group_id", data={"name": sentinel.group_name}
        )

    def test_add_user_to_group(self, h_api, _api_request, h_user):
        h_api.add_user_to_group(h_user, sentinel.group_id)

        _api_request.assert_called_once_with(
            "POST",
            "groups/sentinel.group_id/members/acct:sentinel.username@TEST_AUTHORITY",
        )

    def test__api_request(self, h_api, requests):
        h_api._api_request(sentinel.method, "dummy-path")

        assert requests.request.call_args_list == [
            call(
                # It uses the given HTTP request method.
                method=sentinel.method,
                # It requests the given URL.
                url="https://example.com/private/api/dummy-path",
                # It adds the authentication headers.
                auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
                # Requests time out after 10 seconds.
                timeout=10,
                # It adds the Hypothesis-Application header.
                headers={"Hypothesis-Application": "lms"},
            )
        ]

    def test_if_given_a_data_dict__api_request_dumps_it_to_a_json_string(
        self, h_api, requests
    ):
        h_api._api_request(sentinel.method, "dummy-path", {"a": 1, "b": [2]})

        assert requests.request.call_args[1]["data"] == '{"a":1,"b":[2]}'

    def test_if_given_custom_headers__api_request_adds_them(self, h_api, requests):
        h_api._api_request(
            sentinel.method, "dummy-path", headers={"X-Header": sentinel.header}
        )

        assert requests.request.call_args[1]["headers"]["X-Header"] == sentinel.header

    def test__api_request_raises_HAPINotFoundError_for_404(self, h_api, requests):
        response = Response()
        response.status_code = 404
        exception = RequestException(response=response)
        requests.request.return_value.raise_for_status.side_effect = exception

        with pytest.raises(HAPINotFoundError) as exc_info:
            h_api._api_request(sentinel.method, "dummy-path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    @pytest.mark.parametrize(
        "exception_class",
        [requests_.ConnectionError, HTTPError, ReadTimeout, TooManyRedirects],
    )
    def test__api_request_raises_HAPIError_for_other_http_errors(
        self, h_api, requests, exception_class
    ):
        exception = exception_class()
        requests.request.side_effect = exception

        with pytest.raises(HAPIError) as exc_info:
            h_api._api_request(sentinel.method, "dummy-path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    def test__api_request_raises_other_exceptions_normally(self, h_api, requests):
        requests.request.side_effect = OSError()

        with pytest.raises(OSError):
            h_api._api_request(sentinel.method, "dummy-path")

    @pytest.fixture
    def h_user(self):
        return HUser(
            username=sentinel.username,
            display_name=sentinel.display_name,
            authority="TEST_AUTHORITY",
        )

    @pytest.fixture
    def h_api(self, pyramid_request):
        return HAPI(sentinel.context, pyramid_request)

    @pytest.fixture
    def create_user(self, h_api):
        with patch.object(h_api, "create_user", autospec=True):
            yield h_api.create_user

    @pytest.fixture
    def update_user(self, h_api):
        with patch.object(h_api, "update_user", autospec=True):
            yield h_api.update_user

    @pytest.fixture
    def _api_request(self, h_api):
        with patch.object(h_api, "_api_request", autospec=True):
            yield h_api._api_request

    @pytest.fixture
    def upsert_group_call(self):
        """Return the call that upsert_group() makes to _api_request() to try to upsert the group."""
        return call(
            "PUT",
            "groups/sentinel.group_id",
            data={"groupid": sentinel.group_id, "name": sentinel.group_name},
            headers={"X-Forwarded-User": "acct:lms@TEST_AUTHORITY"},
        )

    @pytest.fixture
    def create_user_call(self):
        """Return the call that create_user() makes to _api_request() to create the lms user."""
        return call(
            "POST",
            "users",
            data={
                "username": "lms",
                "display_name": "",
                "authority": "TEST_AUTHORITY",
                "identities": [{"provider": "lms", "provider_unique_id": "lms"}],
            },
        )


@pytest.fixture(autouse=True)
def requests(patch):
    return patch("lms.services.h_api.requests")
