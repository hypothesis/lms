from unittest.mock import call, create_autospec, sentinel

import pytest
import requests
from h_matchers import Any

from lms.services import CanvasAPIError, ExternalRequestError
from lms.services.canvas_api._basic import BasicClient
from lms.validation import RequestsResponseSchema
from tests import factories


@pytest.mark.usefixtures("http_session")
class TestBasicClient:
    @pytest.mark.parametrize(
        "key,value,expected_url",
        (
            (
                "path",
                "irrelevant",
                Any.url.with_scheme("https").with_host("canvas_host"),
            ),
            ("path", "my_custom/path", Any.url.with_path("/api/v1/my_custom/path")),
            ("params", {"a": "A"}, Any.url.with_query({"a": "A"})),
            ("params", None, Any.url.with_query(None)),
            (
                "url_stub",
                "/custom/stub",
                Any.url.with_path(Any.string.matching("^/custom/stub")),
            ),
        ),
    )
    def test_sends_builds_the_right_url(
        self, basic_client, key, value, expected_url, http_session, Schema
    ):
        basic_client.send(
            **{
                "method": "METHOD",
                "path": "default_path/",
                "timeout": sentinel.timeout,
                "schema": Schema,
                key: value,
            }
        )

        http_session.send.assert_called_once_with(
            Any.request.with_url(expected_url), timeout=sentinel.timeout
        )

    @pytest.mark.parametrize("method", ("GET", "POST", "PATCH"))
    def test_send_uses_the_request_method(
        self, basic_client, Schema, method, http_session
    ):
        basic_client.send(method, "path/", schema=Schema, timeout=sentinel.timeout)

        assert http_session.send.call_args[0][0] == Any.request(method)

    def test_send_sets_pagination_for_multi_schema(
        self, basic_client, PaginatedSchema, http_session
    ):
        basic_client.send(
            "METHOD", "path/", schema=PaginatedSchema, timeout=sentinel.timeout
        )

        expected_url = Any.url.containing_query(
            {"per_page": str(BasicClient.PAGINATION_PER_PAGE)}
        )
        http_session.send.assert_called_once_with(
            Any.request.with_url(expected_url), timeout=sentinel.timeout
        )

    def test_send_calls_the_schema(self, basic_client, http_session, Schema):
        result = basic_client.send(
            "METHOD", "path/", schema=Schema, timeout=sentinel.timeout
        )

        Schema.assert_called_once_with(http_session.send.return_value)
        Schema.return_value.parse.assert_called_once_with()

        assert result == Schema.return_value.parse.return_value

    def test_send_raises_CanvasAPIError_for_error_responses(
        self, basic_client, http_session, Schema
    ):
        http_session.send.return_value = factories.requests.Response(status_code=501)

        with pytest.raises(CanvasAPIError) as exc_info:
            basic_client.send(
                "METHOD", "path/", schema=Schema, timeout=sentinel.timeout
            )

        # The request that was sent.
        request = http_session.send.call_args[0][0]

        # The response that was received.
        response = http_session.send.return_value

        exc = exc_info.value
        assert exc.request == request
        assert exc.response == response

    def test_send_raises_CanvasAPIError_for_networking_errors(
        self, basic_client, http_session, Schema
    ):
        http_session.send.side_effect = requests.ReadTimeout()

        with pytest.raises(CanvasAPIError) as exc_info:
            basic_client.send(
                "METHOD", "path/", schema=Schema, timeout=sentinel.timeout
            )

        # The request that was sent.
        request = http_session.send.call_args[0][0]

        exc = exc_info.value
        assert exc.request == request
        assert exc.response is None

    def test_send_raises_CanvasAPIError_for_validation_errors(
        self, basic_client, Schema, http_session
    ):
        Schema.return_value.parse.side_effect = ExternalRequestError(
            validation_errors=sentinel.validation_errors
        )

        with pytest.raises(CanvasAPIError) as exc_info:
            basic_client.send("any", "any", schema=Schema, timeout=sentinel.timeout)

        # The request that was sent.
        request = http_session.send.call_args[0][0]

        # The response that was received.
        response = http_session.send.return_value

        exc = exc_info.value
        assert exc.request == request
        assert exc.response == response

    @pytest.mark.usefixtures("with_paginated_results")
    def test_send_follows_pagination_links_for_many_schema(
        self, basic_client, PaginatedSchema, http_session
    ):
        result = basic_client.send(
            "METHOD", "path/", schema=PaginatedSchema, timeout=sentinel.timeout
        )

        # Values are from the PaginatedSchema fixture
        assert result == ["item_0", "item_1", "item_2"]

        # We'd love to say the first call here isn't to 'next_url', but we
        # mutate the object in place, so the information is destroyed

        assert http_session.send.call_args_list == [
            call(Any.request(), timeout=sentinel.timeout),
            call(
                Any.request(url="http://example.com/next/0"),
                timeout=sentinel.timeout,
            ),
            call(
                Any.request(url="http://example.com/next/1"),
                timeout=sentinel.timeout,
            ),
        ]

    @pytest.mark.usefixtures("with_paginated_results")
    def test_send_only_paginates_to_the_max_value(self, basic_client, PaginatedSchema):
        basic_client.PAGINATION_MAXIMUM_REQUESTS = 2

        result = basic_client.send(
            "METHOD", "path/", schema=PaginatedSchema, timeout=sentinel.timeout
        )

        assert result == ["item_0", "item_1"]

    @pytest.mark.usefixtures("with_paginated_results")
    def test_send_raises_CanvasAPIError_for_pagination_with_non_many_schema(
        self, basic_client, Schema, http_session, paginated_responses
    ):
        with pytest.raises(CanvasAPIError) as exc_info:
            basic_client.send(
                "METHOD", "path/", schema=Schema, timeout=sentinel.timeout
            )

        # The request that was sent.
        request = http_session.send.call_args[0][0]

        # The response that was received.
        response = paginated_responses[0]

        exc = exc_info.value
        assert exc.request == request
        assert exc.response == response

    @pytest.fixture(autouse=True)
    def has_ok_response(self, http_session):
        http_session.send.return_value = factories.requests.Response(status_code=200)

    @pytest.fixture
    def Schema(self):
        Schema = create_autospec(RequestsResponseSchema)
        Schema.many = False

        return Schema

    @pytest.fixture
    def PaginatedSchema(self, Schema):
        Schema.many = True

        Schema.return_value.parse.side_effect = (
            [f"item_{i}"] for i in range(100)
        )  # pragma: no cover

        return Schema

    @pytest.fixture
    def paginated_responses(self):
        next_url = "http://example.com/next/"
        return [
            factories.requests.Response(
                status_code=200, headers=self.link_headers(next_url + "0")
            ),
            factories.requests.Response(
                status_code=200, headers=self.link_headers(next_url + "1")
            ),
            factories.requests.Response(status_code=200),
        ]

    @pytest.fixture
    def with_paginated_results(self, http_session, paginated_responses):
        http_session.send.side_effect = paginated_responses

    @classmethod
    def link_headers(cls, next_url):
        # See: https://canvas.instructure.com/doc/api/file.pagination.html

        decoy_url = "http://example.com/decoy"

        return {
            "Link": ", ".join(
                [
                    f'<{decoy_url}>; rel="current"',
                    f'<{next_url}>; rel="next"',
                    f'<{decoy_url}>; rel="first"',
                    f'<{decoy_url}>; rel="last"',
                ]
            )
        }
