import json
from datetime import UTC, datetime, timezone
from unittest.mock import call, patch, sentinel

import pytest
from h_api.bulk_api.model.command import ConfigCommand
from h_matchers import Any

from lms.models import HUser
from lms.services import HAPIError
from lms.services.h_api import HAPI, service_factory
from lms.services.http import ExternalRequestError
from tests import factories


class TestHAPI:
    # We're accessing h_api._api_request a lot in this test class, so disable
    # protected-access messages.

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
        "status_code,rows,expected_result",
        (
            (
                200,
                [{"author": {"username": "user1"}}, {"author": {"username": "user2"}}],
                [
                    {
                        "author": {
                            "username": "user1",
                            "userid": "acct:user1@lms.hypothes.is",
                        }
                    },
                    {
                        "author": {
                            "username": "user2",
                            "userid": "acct:user2@lms.hypothes.is",
                        }
                    },
                ],
            ),
            (200, [{"author": {"any": "dict"}}], [{"author": {"any": "dict"}}]),
            (200, [{"any": "dict"}], [{"any": "dict"}]),
            (204, [], []),
        ),
    )
    def test_get_annotations(
        self, h_api, http_service, status_code, rows, expected_result
    ):
        http_service.request.return_value = factories.requests.Response(
            status_code=status_code,
            raw="\n".join(json.dumps(item) for item in rows),
        )

        result = h_api.get_annotations(
            h_userid="acct:name@lms.hypothes.is",
            created_after=datetime(2001, 2, 3, 4, 5, 6),
            created_before=datetime(2002, 2, 3, 4, 5, 6, tzinfo=UTC),
        )

        result = list(result)

        http_service.request.assert_called_once_with(
            method="POST",
            url="https://h.example.com/private/api/bulk/annotation",
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
                        "username": "name",
                        "created": {
                            "gt": "2001-02-03T04:05:06+00:00",
                            "lte": "2002-02-03T04:05:06+00:00",
                        },
                    },
                }
            ),
            stream=True,
            timeout=(60, 60),
        )

        assert result == expected_result

    @pytest.mark.parametrize(
        "kwargs,payload",
        [
            (
                {
                    "group_authority_ids": ["group_1", "group_2"],
                    "group_by": "user",
                    "resource_link_ids": ["assignment_id"],
                },
                {
                    "group_by": "user",
                    "filter": {
                        "groups": ["group_1", "group_2"],
                        "assignment_ids": ["assignment_id"],
                    },
                },
            ),
            (
                {
                    "group_authority_ids": ["group_1", "group_2"],
                    "group_by": "user",
                    "resource_link_ids": ["assignment_id"],
                    "h_userids": ["user_1", "user_2"],
                },
                {
                    "group_by": "user",
                    "filter": {
                        "groups": ["group_1", "group_2"],
                        "assignment_ids": ["assignment_id"],
                        "h_userids": ["user_1", "user_2"],
                    },
                },
            ),
        ],
    )
    def test_get_annotation_counts(self, h_api, http_service, kwargs, payload):
        http_service.request.return_value = factories.requests.Response(raw="{}")

        h_api.get_annotation_counts(**kwargs)

        http_service.request.assert_called_once_with(
            method="POST",
            url="https://h.example.com/private/api/bulk/lms/annotations",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            headers={
                "Content-Type": "application/vnd.hypothesis.v1+json",
                "Hypothesis-Application": "lms",
            },
            data=json.dumps(payload),
            timeout=(60, 60),
            stream=False,
        )

    def test_get_annotation_counts_with_no_groups(self, h_api, http_service):
        assert not h_api.get_annotation_counts(
            group_authority_ids=[], group_by=sentinel.group_by
        )
        http_service.request.assert_not_called()

    def test_get_groups(self, h_api, http_service):
        groups = [
            {"authority_provided_id": "group_1"},
            {"authority_provided_id": "group_2"},
        ]

        http_service.request.side_effect = [
            factories.requests.Response(raw=json.dumps(groups[0])),
            factories.requests.Response(raw=json.dumps(groups[1])),
        ]

        result = h_api.get_groups(
            groups=["group_1", "group_2"],
            annotations_created_after=datetime(2001, 2, 3, 4, 5, 6),
            annotations_created_before=datetime(2002, 2, 3, 4, 5, 6, tzinfo=UTC),
            batch_size=1,
        )

        result = list(result)

        http_service.request.assert_has_calls(
            [
                call(
                    method="POST",
                    url="https://h.example.com/private/api/bulk/group",
                    auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
                    headers={
                        "Hypothesis-Application": "lms",
                        "Content-Type": "application/vnd.hypothesis.v1+json",
                        "Accept": "application/vnd.hypothesis.v1+x-ndjson",
                    },
                    data=json.dumps(
                        {
                            "filter": {
                                "groups": ["group_1"],
                                "annotations_created": {
                                    "gt": "2001-02-03T04:05:06+00:00",
                                    "lte": "2002-02-03T04:05:06+00:00",
                                },
                            },
                        }
                    ),
                    stream=True,
                    timeout=(60, 60),
                ),
                call(
                    method="POST",
                    url="https://h.example.com/private/api/bulk/group",
                    auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
                    headers={
                        "Hypothesis-Application": "lms",
                        "Content-Type": "application/vnd.hypothesis.v1+json",
                        "Accept": "application/vnd.hypothesis.v1+x-ndjson",
                    },
                    data=json.dumps(
                        {
                            "filter": {
                                "groups": ["group_2"],
                                "annotations_created": {
                                    "gt": "2001-02-03T04:05:06+00:00",
                                    "lte": "2002-02-03T04:05:06+00:00",
                                },
                            },
                        }
                    ),
                    stream=True,
                    timeout=(60, 60),
                ),
            ]
        )

        assert result == [
            HAPI.HAPIGroup(authority_provided_id=group["authority_provided_id"])
            for group in groups
        ]

    def test__api_request(self, h_api, http_service):
        h_api._api_request(sentinel.method, "dummy-path", body=sentinel.raw_body)  # noqa: SLF001

        assert http_service.request.call_args_list == [
            call(
                method=sentinel.method,
                url="https://h.example.com/private/api/dummy-path",
                # It adds the authentication headers.
                auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
                headers={"Hypothesis-Application": "lms"},
                stream=False,
                timeout=(60, 60),
                data=sentinel.raw_body,
            )
        ]

    def test_if_given_custom_headers__api_request_adds_them(self, h_api, http_service):
        h_api._api_request(  # noqa: SLF001
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
            h_api._api_request(sentinel.method, "dummy-path")  # noqa: SLF001

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    def test__api_request_raises_other_exceptions_normally(self, h_api, http_service):
        http_service.request.side_effect = OSError()

        with pytest.raises(OSError):
            h_api._api_request(sentinel.method, "dummy-path")  # noqa: SLF001

    def test_get_userid(self, h_api):
        assert h_api.get_userid("username") == "acct:username@lms.hypothes.is"

    def test_get_username(self, h_api):
        assert h_api.get_username("acct:username@lms.hypothes.is") == "username"

    def test_get_username_raises_if_username_is_invalid(self, h_api):
        with pytest.raises(ValueError):
            h_api.get_username("invalid_userid")

    @pytest.fixture
    def BulkAPI(self, patch):
        return patch("lms.services.h_api.BulkAPI")

    @pytest.fixture
    def h_api(self, http_service):
        return HAPI(
            authority="lms.hypothes.is",
            client_id="TEST_CLIENT_ID",
            client_secret="TEST_CLIENT_SECRET",
            h_private_url="https://h.example.com/private/api/",
            http_service=http_service,
        )

    @pytest.fixture
    def _api_request(self, h_api):
        with patch.object(h_api, "_api_request", autospec=True):
            yield h_api._api_request  # noqa: SLF001


class TestServiceFactory:
    def test_it(self, HAPI, pyramid_request, http_service):
        pyramid_request.registry.settings = {
            "h_authority": sentinel.h_authority,
            "h_client_id": sentinel.h_client_id,
            "h_client_secret": sentinel.h_client_secret,
            "h_api_url_private": sentinel.h_api_url_private,
        }

        svc = service_factory(sentinel.context, pyramid_request)

        HAPI.assert_called_once_with(
            authority=sentinel.h_authority,
            client_id=sentinel.h_client_id,
            client_secret=sentinel.h_client_secret,
            h_private_url=sentinel.h_api_url_private,
            http_service=http_service,
        )
        assert svc == HAPI.return_value

    @pytest.fixture
    def HAPI(self, patch):
        return patch("lms.services.h_api.HAPI")
