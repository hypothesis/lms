from unittest.mock import call, patch, sentinel

import pytest
from h_api.bulk_api.model.command import ConfigCommand
from h_matchers import Any
from requests import RequestException

from lms.models import HUser
from lms.services import HAPIError
from lms.services.h_api import HAPI


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

        assert user == HUser(username="username", display_name=sentinel.display_name)

    def test_bulk_action_process_commands_correctly(self, h_api, BulkAPI):
        h_api.bulk_action(
            [sentinel.command_1, sentinel.command_2,]
        )

        BulkAPI.to_string.assert_called_once_with(
            [
                Any.object(ConfigCommand).with_attrs(
                    {
                        "body": Any.object.with_attrs(
                            {
                                "effective_user": "acct:lms@TEST_AUTHORITY",
                                "total_instructions": 3,
                            }
                        )
                    }
                ),
                sentinel.command_1,
                sentinel.command_2,
            ]
        )

    def test_bulk_action_calls_h_correctly(self, h_api, BulkAPI, _api_request):
        h_api.bulk_action([sentinel.command])

        _api_request.assert_called_once_with(
            "POST",
            path="bulk",
            body=BulkAPI.to_string.return_value,
            headers=Any.mapping.containing(
                {"Content-Type": "application/vnd.hypothesis.v1+x-ndjson"}
            ),
        )

    @pytest.fixture
    def BulkAPI(self, patch):
        return patch("lms.services.h_api.BulkAPI")

    def test__api_request(self, h_api, requests):
        h_api._api_request(sentinel.method, "dummy-path", body=sentinel.raw_body)

        assert requests.request.call_args_list == [
            call(
                method=sentinel.method,
                url="https://example.com/private/api/dummy-path",
                # It adds the authentication headers.
                auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
                timeout=10,
                headers={"Hypothesis-Application": "lms"},
                data=sentinel.raw_body,
            )
        ]

    def test_if_given_custom_headers__api_request_adds_them(self, h_api, requests):
        h_api._api_request(
            sentinel.method, "dummy-path", headers={"X-Header": sentinel.header}
        )

        assert requests.request.call_args[1]["headers"] == Any.mapping.containing(
            {"X-Header": sentinel.header}
        )

    def test__api_request_raises_HAPIError_for_http_errors(self, h_api, requests):
        exception = RequestException("Foo")
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
    def h_api(self, pyramid_request):
        return HAPI(sentinel.context, pyramid_request)

    @pytest.fixture
    def _api_request(self, h_api):
        with patch.object(h_api, "_api_request", autospec=True):
            yield h_api._api_request

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
