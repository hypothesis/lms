import json
from datetime import datetime, timezone
from unittest.mock import call, patch, sentinel

import pytest
from h_api.bulk_api.model.command import ConfigCommand
from h_matchers import Any

from lms.models import HUser
from lms.services import HAPIError
from lms.services.h_api import HAPI
from lms.services.http import ExternalRequestError
from tests import factories
from tests.conftest import TEST_SETTINGS


@pytest.mark.usefixtures("http_service")
class TestHAPI:
    # We're accessing h_api._api_request a lot in this test class, so disable
    # protected-access messages.
    # pylint: disable=protected-access

    def test_bulk_action_process_commands_correctly(self, h_api, BulkAPI):
        h_api.execute_bulk([sentinel.command_1, sentinel.command_2])

        BulkAPI.to_string.assert_called_once_with(
            [
                Any.object(ConfigCommand).with_attrs(
                    {
                        "body": Any.object.with_attrs(
                            {
                                "effective_user": "acct:lms@lms.hypothes.is",
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
        h_api.execute_bulk([sentinel.command])

        _api_request.assert_called_once_with(
            "POST",
            path="bulk",
            body=BulkAPI.to_string.return_value,
            headers=Any.mapping.containing(
                {"Content-Type": "application/vnd.hypothesis.v1+x-ndjson"}
            ),
        )

    def test_get_user_works(self, h_api, _api_request):
        _api_request.return_value.json.return_value = {
            "display_name": sentinel.display_name
        }

        user = h_api.get_user("username")

        _api_request.assert_called_once_with(
            "GET", path="users/acct:username@lms.hypothes.is"
        )

        assert user == HUser(username="username", display_name=sentinel.display_name)

    @pytest.mark.parametrize(
        "status_code,rows", ((200, [{"any": "value"}, {"another": "value"}]), (204, []))
    )
    def test_get_annotations(self, h_api, http_service, status_code, rows):
        http_service.request.return_value = factories.requests.Response(
            status_code=status_code,
            raw="\n".join(json.dumps(item) for item in rows),
        )

        result = h_api.get_annotations(
            audience_usernames=["name_1", "name_2"],
            updated_after=datetime(2001, 2, 3, 4, 5, 6),
            updated_before=datetime(2002, 2, 3, 4, 5, 6, tzinfo=timezone.utc),
        )

        result = list(result)

        http_service.request.assert_called_once_with(
            method="POST",
            url="https://h.example.com/private/api/bulk",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            headers={
                "Hypothesis-Application": "lms",
                "Content-Type": "application/vnd.hypothesis.v1+json",
                "Accept": "application/vnd.hypothesis.v1+x-ndjson",
            },
            data=json.dumps(
                {
                    "filter": {
                        "limit": 100000,
                        "audience": {"username": ["name_1", "name_2"]},
                        "updated": {
                            "gt": "2001-02-03T04:05:06+00:00",
                            "lte": "2002-02-03T04:05:06+00:00",
                        },
                    },
                    "fields": ["author.username", "group.authority_provided_id"],
                }
            ),
            stream=True,
        )

        assert result == rows

    def test__api_request(self, h_api, http_service):
        h_api._api_request(sentinel.method, "dummy-path", body=sentinel.raw_body)

        assert http_service.request.call_args_list == [
            call(
                method=sentinel.method,
                url=TEST_SETTINGS["h_api_url_private"] + "dummy-path",
                # It adds the authentication headers.
                auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
                headers={"Hypothesis-Application": "lms"},
                stream=False,
                data=sentinel.raw_body,
            )
        ]

    def test_if_given_custom_headers__api_request_adds_them(self, h_api, http_service):
        h_api._api_request(
            sentinel.method, "dummy-path", headers={"X-Header": sentinel.header}
        )

        assert http_service.request.call_args[1]["headers"] == Any.mapping.containing(
            {"X-Header": sentinel.header}
        )

    def test__api_request_raises_HAPIError_for_request_errors(
        self, h_api, http_service
    ):
        exception = ExternalRequestError()
        http_service.request.side_effect = exception

        with pytest.raises(HAPIError) as exc_info:
            h_api._api_request(sentinel.method, "dummy-path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    def test__api_request_raises_other_exceptions_normally(self, h_api, http_service):
        http_service.request.side_effect = OSError()

        with pytest.raises(OSError):
            h_api._api_request(sentinel.method, "dummy-path")

    @pytest.fixture
    def BulkAPI(self, patch):
        return patch("lms.services.h_api.BulkAPI")

    @pytest.fixture
    def h_api(self, pyramid_request):
        return HAPI(sentinel.context, pyramid_request)

    @pytest.fixture
    def _api_request(self, h_api):
        with patch.object(h_api, "_api_request", autospec=True):
            yield h_api._api_request
