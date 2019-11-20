from unittest.mock import patch, sentinel

import pytest
from h_matchers import Any
from pyramid.testing import DummyRequest
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

BASE_URL = "http://example.com/base/"
AUTHORITY = "test-authority"


class TestHAPI:
    def test_get_user_works(self, hapi):
        hapi._api_request.return_value.json.return_value = {
            "display_name": sentinel.display_name
        }
        user = hapi.get_user("username")

        hapi._api_request.assert_called_once_with(
            "GET", path="users/acct:username@test-authority"
        )

        assert user == Any.instance_of(HUser)
        assert user.authority == AUTHORITY
        assert user.username == "username"
        assert user.display_name == sentinel.display_name

    def test_create_user_works(self, hapi, h_user):
        hapi.create_user(h_user, sentinel.provider, sentinel.provider_unique_id)

        hapi._api_request.assert_called_once_with(
            "POST",
            "users",
            data={
                "username": h_user.username,
                "display_name": h_user.display_name,
                "authority": AUTHORITY,
                "identities": [
                    {
                        "provider": sentinel.provider,
                        "provider_unique_id": sentinel.provider_unique_id,
                    }
                ],
            },
        )

    def test_update_user_works(self, hapi, h_user):
        hapi.update_user(h_user)

        hapi._api_request.assert_called_once_with(
            "PATCH",
            "users/sentinel.username",
            data={"display_name": h_user.display_name},
        )

    @patch.object(HAPI, "create_user")
    @patch.object(HAPI, "update_user")
    def test_upsert_calls_calls_create_if_update_fails(
        self, update_user, create_user, hapi, h_user
    ):
        update_user.side_effect = HAPINotFoundError()
        hapi.upsert_user(h_user, sentinel.provider, sentinel.provider_unique_id)

        update_user.assert_called_once_with(h_user)
        create_user.assert_called_once_with(
            h_user, sentinel.provider, sentinel.provider_unique_id
        )

    def test_create_groups_works(self, hapi, h_user):
        hapi.create_group(sentinel.group_id, sentinel.group_name, h_user)

        hapi._api_request.assert_called_once_with(
            "PUT",
            "groups/sentinel.group_id",
            data={"groupid": sentinel.group_id, "name": sentinel.group_name},
            headers=Any.dict.containing({"X-Forwarded-User": h_user.userid}),
        )

    def test_update_group_works(self, hapi):
        hapi.update_group(sentinel.group_id, sentinel.group_name)

        hapi._api_request.assert_called_once_with(
            "PATCH", "groups/sentinel.group_id", data={"name": sentinel.group_name}
        )

    def test_add_user_to_group(self, hapi, h_user):
        hapi.add_user_to_group(h_user, sentinel.group_id)

        hapi._api_request.assert_called_once_with(
            "POST",
            "groups/sentinel.group_id/members/acct:sentinel.username@test-authority",
        )

    @pytest.fixture
    def h_user(self):
        return HUser(
            username=sentinel.username,
            display_name=sentinel.display_name,
            authority=AUTHORITY,
        )

    @pytest.yield_fixture
    def hapi(self, p_request):
        hapi = HAPI(sentinel.context, p_request)

        with patch.object(HAPI, "_api_request"):
            yield hapi


class TestHAPIRequest:
    def test_it_passes_expected_defaults(self, hapi, requests):
        hapi._api_request(sentinel.method, "dummy-path")

        self._assert_called_requests_with(
            requests, auth=(sentinel.client_id, sentinel.client_secret), timeout=10
        )

    def test_it_passes_method_and_path(self, hapi, requests):
        hapi._api_request(sentinel.method, "/path")

        self._assert_called_requests_with(
            requests, method=sentinel.method, url=BASE_URL + "path",
        )

    def test_id_dumps_json_body(self, hapi, requests):
        hapi._api_request(sentinel.method, "dummy-path", {"a": 1, "b": [2]})

        self._assert_called_requests_with(requests, data='{"a":1,"b":[2]}')

    def test_it_adds_expected_headers(self, hapi, requests):
        hapi._api_request(
            sentinel.method, "dummy-path", headers={"X-Header": sentinel.header}
        )

        self._assert_called_requests_with(
            requests,
            headers={"X-Header": sentinel.header, "Hypothesis-Application": "lms"},
        )

    def test_it_raises_HAPINotFoundError_for_404(self, hapi, requests):
        response = Response()
        response.status_code = 404
        exception = RequestException(response=response)
        requests.request.return_value.raise_for_status.side_effect = exception

        with pytest.raises(HAPINotFoundError) as exc_info:
            hapi._api_request(sentinel.method, "dummy-path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    @pytest.mark.parametrize(
        "exception", [ConnectionError(), HTTPError(), ReadTimeout(), TooManyRedirects()]
    )
    def test_it_raises_HAPIError_for_other_http_errors(self, hapi, requests, exception):
        requests.request.side_effect = exception

        with pytest.raises(HAPIError) as exc_info:
            hapi._api_request(sentinel.method, "dummy-path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    def test_other_exceptions_are_raised_normally(self, hapi, requests):
        requests.request.side_effect = OSError()

        with pytest.raises(OSError):
            hapi._api_request(sentinel.method, "dummy-path")

    def _assert_called_requests_with(self, requests, **extras):
        values = {
            "method": Any(),
            "url": Any(),
            "auth": Any(),
            "timeout": Any(),
            "headers": Any(),
        }

        values.update(extras)

        requests.request.assert_called_once_with(**values)

    @pytest.fixture
    def hapi(self, p_request):
        return HAPI(sentinel.context, p_request)


@pytest.fixture(autouse=True)
def requests(patch):
    return patch("lms.services.h_api.requests")


@pytest.fixture
def p_request():
    pyramid_request = DummyRequest()

    pyramid_request.registry.settings = {
        "h_client_id": sentinel.client_id,
        "h_client_secret": sentinel.client_secret,
        "h_api_url_private": BASE_URL,
        "h_authority": AUTHORITY,
    }

    return pyramid_request
