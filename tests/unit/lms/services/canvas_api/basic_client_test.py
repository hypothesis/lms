import json
from io import BytesIO
from unittest.mock import MagicMock, call, create_autospec, sentinel

import pytest
from h_matchers import Any
from requests import Request, RequestException, Response

from lms.services import CanvasAPIError
from lms.services.canvas_api import BasicClient
from lms.validation import RequestsResponseSchema, ValidationError


class TestBasicClient:
    @pytest.mark.parametrize(
        "key,value,expected_url",
        (
            (
                "path",
                "irrelevant",
                Any.url.with_scheme("https").with_host("canvas_host"),
            ),
            ("path", "my_custom/path", Any.url.with_path("/_api/v1/my_custom/path")),
            ("params", {"a": "A"}, Any.url.with_query({"a": "A"})),
            (
                "url_stub",
                "/custom/stub",
                Any.url.with_path(Any.string.matching("^/custom/stub")),
            ),
        ),
    )
    def test_get_url(self, basic_client, key, value, expected_url):
        url = basic_client.get_url(**{"path": "default_path", key: value})

        assert url == expected_url

    @pytest.mark.parametrize(
        "params,expected_params", ((None, None), ({"a": "A"}, {"a": "A"}),)
    )
    def test_make_request(self, basic_client, params, expected_params, Schema):
        request = basic_client.make_request("GET", "path", schema=Schema, params=params)

        assert request == Any.request(
            method="GET",
            url=Any.url.matching(basic_client.get_url("path")).with_query(
                expected_params
            ),
        )

    @pytest.mark.parametrize("params", ((None, {"a": "A"})))
    def test_make_request_sets_pagination_for_multi_schema(
        self, basic_client, params, PaginatedSchema
    ):
        request = basic_client.make_request(
            "GET", "path", schema=PaginatedSchema, params=params
        )

        assert request == Any.request.with_url(
            Any.url.containing_query({"per_page": str(BasicClient.PAGINATION_PER_PAGE)})
        )

    def test_send_and_validate(self, basic_client, http_session, Schema):
        response = self._make_response("request_body")
        http_session.send.return_value = response

        basic_client.send_and_validate(sentinel.request, Schema)

        http_session.send.assert_called_once_with(sentinel.request, timeout=9)
        Schema.assert_called_once_with(response)
        Schema.return_value.parse.assert_called_once_with()

    def test_it_raises_CanvasAPIError_for_request_errors(
        self, basic_client, http_session, Schema
    ):
        response = self._make_response("request_body")
        response.raise_for_status = MagicMock()
        response.raise_for_status.side_effect = RequestException

        http_session.send.return_value = response

        with pytest.raises(CanvasAPIError):
            basic_client.send_and_validate(sentinel.request, Schema)

    def test_send_and_validate_raises_CanvasAPIError_for_validation_errors(
        self, basic_client, Schema
    ):
        Schema.return_value.parse.side_effect = ValidationError("Some error")

        with pytest.raises(CanvasAPIError):
            basic_client.send_and_validate(sentinel.request, Schema)

    @pytest.mark.usefixtures("paginated_results")
    def test_send_and_validate_follows_pagination_links_for_many_schema(
        self, basic_client, PaginatedSchema, http_session
    ):
        result = basic_client.send_and_validate(
            Request("method", "http://example.com/start").prepare(), PaginatedSchema
        )

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
    def test_send_and_validate_only_paginates_to_the_max_value(
        self, basic_client, PaginatedSchema
    ):
        basic_client.PAGINATION_MAXIMUM_REQUESTS = 2

        result = basic_client.send_and_validate(sentinel.request, PaginatedSchema)

        assert result == ["item_0", "item_1"]

    @pytest.mark.usefixtures("paginated_results")
    def test_send_and_validate_raises_CanvasAPIError_for_pagination_with_non_many_schema(
        self, basic_client, Schema
    ):
        with pytest.raises(CanvasAPIError):
            basic_client.send_and_validate(sentinel.request, Schema)

    @pytest.fixture
    def requests(self, patch):
        return patch("lms.services.canvas_api.requests")

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
            self._make_response(headers=self._link_headers(next_url + "0")),
            self._make_response(headers=self._link_headers(next_url + "1")),
            self._make_response(),
        ]

    @pytest.fixture(autouse=True)
    def http_session(self, patch):
        session = patch("lms.services.canvas_api.basic_client.Session")

        return session()

    @classmethod
    def _link_headers(cls, next_url):
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

    @classmethod
    def _make_response(cls, json_data=None, raw=None, status_code=200, headers=None):
        response = Response()

        if raw is None:
            raw = json.dumps(json_data)

        response.raw = BytesIO(raw.encode("utf-8"))
        response.status_code = status_code

        if headers:
            # Requests seems to store these lower case and expects them that way
            response.headers = {key.lower(): value for key, value in headers.items()}

        return response
