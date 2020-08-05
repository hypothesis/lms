from unittest.mock import call, create_autospec

import pytest
from h_matchers import Any

from lms.services import CanvasAPIError
from lms.services.canvas_api._basic import BasicClient
from lms.validation import RequestsResponseSchema, ValidationError
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
                "schema": Schema,
                key: value,
            }
        )

        http_session.send.assert_called_once_with(
            Any.request.with_url(expected_url), timeout=Any()
        )

    @pytest.mark.parametrize("method", ("GET", "POST", "PATCH"))
    def test_send_uses_the_request_method(
        self, basic_client, Schema, method, http_session
    ):
        basic_client.send(method, "path/", schema=Schema)

        http_session.send.assert_called_once_with(Any.request(method), timeout=Any())

    def test_send_sets_pagination_for_multi_schema(
        self, basic_client, PaginatedSchema, http_session
    ):
        basic_client.send("METHOD", "path/", schema=PaginatedSchema)

        expected_url = Any.url.containing_query(
            {"per_page": str(BasicClient.PAGINATION_PER_PAGE)}
        )
        http_session.send.assert_called_once_with(
            Any.request.with_url(expected_url), timeout=Any()
        )

    def test_send_calls_the_schema(self, basic_client, http_session, Schema):
        result = basic_client.send("METHOD", "path/", schema=Schema)

        Schema.assert_called_once_with(http_session.send.return_value)
        Schema.return_value.parse.assert_called_once_with()

        assert result == Schema.return_value.parse.return_value

    def test_send_raises_CanvasAPIError_for_request_errors(
        self, basic_client, http_session, Schema
    ):
        http_session.set_response(status_code=501)

        with pytest.raises(CanvasAPIError):
            basic_client.send("METHOD", "path/", schema=Schema)

    def test_send_raises_CanvasAPIError_for_validation_errors(
        self, basic_client, Schema
    ):
        Schema.return_value.parse.side_effect = ValidationError("Some error")

        with pytest.raises(CanvasAPIError):
            basic_client.send("any", "any", schema=Schema)

    @pytest.mark.usefixtures("paginated_results")
    def test_send_follows_pagination_links_for_many_schema(
        self, basic_client, PaginatedSchema, http_session
    ):
        result = basic_client.send("METHOD", "path/", schema=PaginatedSchema)

        # Values are from the PaginatedSchema fixture
        assert result == ["item_0", "item_1", "item_2"]

        # We'd love to say the first call here isn't to 'next_url', but we
        # mutate the object in place, so the information is destroyed

        http_session.send.assert_has_calls(
            [
                call(Any.request(), timeout=Any()),
                call(Any.request(url="http://example.com/next/0"), timeout=Any()),
                call(Any.request(url="http://example.com/next/1"), timeout=Any()),
            ]
        )

    @pytest.mark.usefixtures("paginated_results")
    def test_send_only_paginates_to_the_max_value(self, basic_client, PaginatedSchema):
        basic_client.PAGINATION_MAXIMUM_REQUESTS = 2

        result = basic_client.send("METHOD", "path/", schema=PaginatedSchema)

        assert result == ["item_0", "item_1"]

    @pytest.mark.usefixtures("paginated_results")
    def test_send_raises_CanvasAPIError_for_pagination_with_non_many_schema(
        self, basic_client, Schema
    ):
        with pytest.raises(CanvasAPIError):
            basic_client.send("METHOD", "path/", schema=Schema)

    @pytest.fixture(autouse=True)
    def has_ok_response(self, http_session):
        http_session.set_response()

    @pytest.fixture
    def Schema(self):
        # pylint: disable=invalid-name
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
    def paginated_results(self, http_session):
        next_url = "http://example.com/next/"
        http_session.send.side_effect = [
            factories.requests.Response(
                status_code=200, headers=self.link_headers(next_url + "0")
            ),
            factories.requests.Response(
                status_code=200, headers=self.link_headers(next_url + "1")
            ),
            factories.requests.Response(status_code=200),
        ]

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
