import json
from io import BytesIO
from unittest import mock
from unittest.mock import call, create_autospec, sentinel

import pytest
from _pytest.mark import param
from h_matchers import Any
from h_matchers.decorator import fluent_entrypoint
from h_matchers.matcher.core import Matcher
from requests import PreparedRequest, Request, RequestException, Response

from lms.models import ApplicationInstance, OAuth2Token
from lms.services import CanvasAPIAccessTokenError, CanvasAPIError, CanvasAPIServerError
from lms.services.canvas_api import CanvasAPIClient, _CanvasAPIAuthenticatedClient
from lms.validation import RequestsResponseSchema, ValidationError

# pylint: disable=protected-access


class AnyRequest(Matcher):  # pragma: no cover
    """Matching object for request type objects."""

    # This will be moved out to h-matchers and prettied up and tested there
    # At present the matcher only supports `requests.PreparedRequest` but the
    # plan is to expand it to more request types in future.

    assert_on_comparison = False

    def __init__(self, method=None, url=None, headers=None):
        self.method = method
        self.url = url
        self.headers = headers

        super().__init__(f"<AnyRequest {method}: {url}>", self._matches_request)

    # pylint: disable=function-redefined
    @classmethod
    def containing_headers(cls, headers):
        """Confuse pylint so it doesn't complain about fluent-endpoints."""

    @fluent_entrypoint
    def containing_headers(self, headers):
        self.headers = Any.mapping.containing(headers)

        return self

    def _matches_request(self, other):
        try:
            self.assert_equal_to(other)
        except AssertionError:
            if self.assert_on_comparison:
                raise
            return False

        return True

    def assert_equal_to(self, other):
        if isinstance(other, PreparedRequest):
            if self.method is not None and self.method != other.method:
                raise AssertionError(f"Method '{other.method}' != '{self.method}'")

            if self.url is not None and self.url != other.url:
                raise AssertionError(f"URL '{other.url}' != '{self.url}'")

            if self.headers is not None and self.headers != other.headers:
                raise AssertionError(f"Headers {other.headers} != {self.headers}")

            return

        raise AssertionError(f"Unknown request type '{type(other)}'")


def _make_response(json_data=None, raw=None, status_code=200, headers=None):
    response = Response()

    if raw is None:
        raw = json.dumps(json_data)

    response.raw = BytesIO(raw.encode("utf-8"))
    response.status_code = status_code

    if headers:
        # Requests seems to store these lower case and expects them that way
        response.headers = {key.lower(): value for key, value in headers.items()}

    return response


class TestDataCalls:
    @pytest.mark.usefixtures("access_token")
    def test_authenticated_users_sections(self, api_client, http_session):
        sections = [{"id": 1, "name": "name_1"}, {"id": 2, "name": "name_2"}]
        http_session.send.return_value = _make_response({"sections": sections})

        response = api_client.authenticated_users_sections("COURSE_ID")

        assert response == sections
        http_session.send.assert_called_once_with(
            AnyRequest(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID").with_query(
                    {"include[]": "sections"}
                ),
                headers={"Authorization": "Bearer existing_access_token"},
            ),
            timeout=Any(),
        )

    @pytest.mark.usefixtures("access_token")
    def test_course_sections(self, api_client, http_session):
        sections = [
            {"id": 101, "name": "name_1"},
            {"id": 102, "name": "name_2"},
        ]
        sections_with_noise = [
            dict(section, unexpected="ignored") for section in sections
        ]
        http_session.send.return_value = _make_response(sections_with_noise)

        response = api_client.course_sections("COURSE_ID")

        assert response == sections
        http_session.send.assert_called_once_with(
            AnyRequest(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/sections"),
                headers={"Authorization": "Bearer existing_access_token"},
            ),
            timeout=Any(),
        )

    @pytest.mark.usefixtures("access_token")
    def test_course_section_raises_CanvasAPIError_with_no_sections_returned(
        self, api_client, http_session
    ):
        http_session.send.return_value = _make_response([])

        with pytest.raises(CanvasAPIError):
            api_client.course_sections("dummy")

    @pytest.mark.usefixtures("access_token")
    def test_users_sections(self, api_client, http_session):
        http_session.send.return_value = _make_response(
            {
                "enrollments": [
                    {"course_section_id": 101, "unexpected": "ignored"},
                    {"course_section_id": 102, "unexpected": "ignored"},
                ]
            }
        )

        response = api_client.users_sections("USER_ID", "COURSE_ID")

        assert response == [{"id": 101}, {"id": 102}]
        http_session.send.assert_called_once_with(
            AnyRequest(
                "GET",
                url=Any.url.with_path(
                    "api/v1/courses/COURSE_ID/users/USER_ID"
                ).with_query({"include[]": "enrollments"}),
                headers={"Authorization": "Bearer existing_access_token"},
            ),
            timeout=Any(),
        )

    @pytest.mark.usefixtures("access_token")
    def test_list_files(self, api_client, http_session):
        files = [
            {"display_name": "display_name_1", "id": 1, "updated_at": "updated_at_1"},
            {"display_name": "display_name_1", "id": 1, "updated_at": "updated_at_1"},
        ]
        files_with_noise = [dict(file, unexpected="igored") for file in files]
        http_session.send.return_value = _make_response(files_with_noise)

        response = api_client.list_files("COURSE_ID")

        assert response == files
        AnyRequest.assert_on_comparison = True
        http_session.send.assert_called_once_with(
            AnyRequest(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/files").with_query(
                    {
                        "content_types[]": "application/pdf",
                        "per_page": str(api_client.PAGINATION_PER_PAGE),
                    }
                ),
                headers={"Authorization": "Bearer existing_access_token"},
            ),
            timeout=Any(),
        )

    @pytest.mark.usefixtures("access_token")
    def test_public_url(self, api_client, http_session):
        http_session.send.return_value = _make_response(
            {"public_url": "public_url_value"}
        )

        response = api_client.public_url("FILE_ID")

        assert response == "public_url_value"
        http_session.send.assert_called_once_with(
            AnyRequest(
                "GET",
                url=Any.url.with_path("api/v1/files/FILE_ID/public_url"),
                headers={"Authorization": "Bearer existing_access_token"},
            ),
            timeout=Any(),
        )

    def test_methods_require_access_token(self, data_method):
        with pytest.raises(CanvasAPIAccessTokenError):
            data_method()

    @pytest.mark.usefixtures("access_token")
    def test_methods_raise_CanvasAPIServerError_if_the_response_json_has_the_wrong_format(
        self, data_method, http_session
    ):
        http_session.send.return_value = _make_response({})

        with pytest.raises(CanvasAPIServerError):
            data_method()

    @pytest.mark.usefixtures("access_token")
    def test_methods_raise_CanvasAPIServerError_if_the_response_is_invalid_json(
        self, data_method, http_session
    ):
        http_session.send.return_value = _make_response(raw="[broken json")

        with pytest.raises(CanvasAPIServerError):
            data_method()

    def test_methods_use_retry_mechanism(self, api_client, data_method):
        # The actual test of the retry mechanism is covered elsewhere
        with mock.patch.object(api_client, "make_authenticated_request") as func:
            data_method()

            func.assert_called_once()

    methods = {
        "authenticated_users_sections": ["course_id"],
        "course_sections": ["course_id"],
        "users_sections": ["user_id", "course_id"],
        "list_files": ["course_id"],
        "public_url": ["file_id"],
    }

    @pytest.fixture(params=tuple(methods.items()), ids=tuple(methods.keys()))
    def data_method(self, request, api_client):
        method, args = request.param

        return lambda: getattr(api_client, method)(*args)

    @pytest.fixture
    def api_client(self, pyramid_request):
        return CanvasAPIClient(sentinel.context, pyramid_request)


class TestTokenCalls:
    @pytest.mark.parametrize(
        "json_data",
        (
            {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_in": 3600,
            },
            {"access_token": "test_access_token"},
        ),
    )
    def test_get_token(
        self, base_client, http_session, db_session, pyramid_request, json_data
    ):
        http_session.send.return_value = _make_response(json_data)

        base_client.get_token("authorization_code")

        http_session.send.assert_called_once_with(
            AnyRequest(
                method="POST",
                url=Any.url()
                .with_path("login/oauth2/token")
                .with_query(
                    {
                        "grant_type": "authorization_code",
                        "client_id": "developer_key",
                        "client_secret": "developer_secret",
                        "redirect_uri": base_client._redirect_uri,
                        "code": "authorization_code",
                        "replace_tokens": "True",
                    }
                ),
            ),
            timeout=Any(),
        )
        self._assert_token_is_saved_in_db(db_session, pyramid_request, json_data)

    # Add noise with an existing token to make sure we update it
    @pytest.mark.usefixtures("access_token")
    @pytest.mark.parametrize(
        "json_data",
        (
            {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_in": 3600,
            },
            {"access_token": "test_access_token"},
        ),
    )
    def test__get_refreshed_token(
        self, base_client, http_session, db_session, pyramid_request, json_data
    ):
        http_session.send.return_value = _make_response(json_data)

        base_client._get_refreshed_token("new_refresh_token")

        http_session.send.assert_called_once_with(
            AnyRequest(
                method="POST",
                url=Any.url()
                .with_path("login/oauth2/token")
                .with_query(
                    {
                        "grant_type": "refresh_token",
                        "client_id": "developer_key",
                        "client_secret": "developer_secret",
                        "refresh_token": "new_refresh_token",
                    }
                ),
            ),
            timeout=Any(),
        )

        # We use our own refresh token if none was passed back from Canvas
        json_data.setdefault("refresh_token", "new_refresh_token")
        self._assert_token_is_saved_in_db(db_session, pyramid_request, json_data)

    @pytest.mark.parametrize(
        "json_data",
        (
            param({}, id="No access token"),
            param(
                {"expires_in": -1, "access_token": "irrelevant"},
                id="Negative expires in",
            ),
        ),
    )
    @pytest.mark.parametrize("method", ("get_token", "_get_refreshed_token"))
    def test_token_methods_raises_CanvasAPIServerError_for_bad_responses(
        self, http_session, base_client, method, json_data
    ):
        http_session.send.return_value = _make_response(json_data)

        method = getattr(base_client, method)

        with pytest.raises(CanvasAPIServerError):
            method("token_value")

    def _assert_token_is_saved_in_db(self, db_session, pyramid_request, json_data):
        oauth2_token = db_session.query(OAuth2Token).one()

        assert oauth2_token.user_id == pyramid_request.lti_user.user_id
        assert oauth2_token.consumer_key == pyramid_request.lti_user.oauth_consumer_key

        assert oauth2_token.access_token == json_data["access_token"]
        assert oauth2_token.refresh_token == json_data.get("refresh_token")
        assert oauth2_token.expires_in == json_data.get("expires_in")

    @pytest.fixture(autouse=True)
    def ai_getter(self, ai_getter):
        ai_getter.developer_key.return_value = "developer_key"
        ai_getter.developer_secret.return_value = "developer_secret"

        return ai_getter


class TestValidatedResponse:
    def test_it(self, base_client, http_session, Schema):
        response = _make_response("request_body")
        http_session.send.return_value = response

        base_client._validated_response(sentinel.request, Schema)

        http_session.send.assert_called_once_with(sentinel.request, timeout=9)
        Schema.assert_called_once_with(response)
        Schema.return_value.parse.assert_called_once_with()

    def test_it_raises_CanvasAPIError_for_request_errors(
        self, base_client, http_session, Schema
    ):
        response = _make_response("request_body")
        response.raise_for_status = mock.MagicMock()
        response.raise_for_status.side_effect = RequestException
        http_session.send.return_value = response

        with pytest.raises(CanvasAPIError):
            base_client._validated_response(sentinel.request, Schema)

    @pytest.mark.usefixtures("paginated_results")
    def test_it_follows_pagination_links_for_many_schema(
        self, base_client, http_session, PaginatedSchema
    ):
        result = base_client._validated_response(
            Request("method", "http://example.com/start").prepare(), PaginatedSchema
        )

        # Values are from the PaginatedSchema fixture
        assert result == ["item_0", "item_1", "item_2"]

        # We'd love to say the first call here isn't to 'next_url', but we
        # mutate the object in place, so the information is destroyed
        http_session.send.assert_has_calls(
            [
                call(AnyRequest(), timeout=Any()),
                call(AnyRequest(url="http://example.com/next"), timeout=Any()),
                call(AnyRequest(url="http://example.com/next"), timeout=Any()),
            ]
        )

    @pytest.mark.usefixtures("paginated_results")
    def test_it_only_paginates_to_the_max_value(self, base_client, PaginatedSchema):
        base_client.PAGINATION_MAXIMUM_REQUESTS = 2

        result = base_client._validated_response(sentinel.request, PaginatedSchema)

        assert result == ["item_0", "item_1"]

    @pytest.mark.usefixtures("paginated_results")
    def test_it_raises_CanvasAPIError_for_pagination_with_non_many_schema(
        self, base_client, Schema
    ):
        with pytest.raises(CanvasAPIError):
            base_client._validated_response(sentinel.request, Schema)

    @pytest.fixture
    def paginated_results(self, http_session):
        next_url = "http://example.com/next"
        http_session.send.side_effect = [
            _make_response(headers=self._link_headers(next_url)),
            _make_response(headers=self._link_headers(next_url)),
            _make_response(),
        ]

    def test_it_raises_CanvasAPIError_for_validation_errors(self, base_client, Schema):
        Schema.return_value.parse.side_effect = ValidationError("Some error")

        with pytest.raises(CanvasAPIError):
            base_client._validated_response(sentinel.request, Schema)

    def _link_headers(self, next_url):
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


class TestMakeAuthenticatedRequest:
    def test_it(self, base_client, access_token, Schema):
        params = {"a": "1"}

        base_client.make_authenticated_request(
            method="method", path="path", schema=Schema, params=params
        )

        expected_url = (
            Any.url.matching(f"https://{base_client._canvas_url}")
            .with_path("api/v1/path")
            .with_query(params)
        )
        base_client._validated_response.assert_called_once_with(
            AnyRequest(method="METHOD", url=expected_url).containing_headers(
                {"Authorization": f"Bearer {access_token.access_token}"}
            ),
            Schema,
        )

    @pytest.mark.usefixtures("access_token")
    def test_it_adds_pagination_for_multi_schema(self, base_client, PaginatedSchema):
        base_client.make_authenticated_request(
            method="method", path="path", schema=PaginatedSchema
        )

        AnyRequest.assert_on_comparison = True
        base_client._validated_response.assert_called_once_with(
            AnyRequest(
                url=Any.url.containing_query(
                    {"per_page": str(base_client.PAGINATION_PER_PAGE)}
                )
            ),
            Any(),
        )

    @pytest.mark.usefixtures("access_token")
    def test_it_refreshes_the_token_and_tries_again(self, base_client, Schema):
        base_client._validated_response.side_effect = [
            CanvasAPIAccessTokenError(),
            sentinel.second_call,
        ]
        base_client._get_refreshed_token.return_value = "new_access_token"

        response = base_client.make_authenticated_request(
            method="method", path="path", schema=Schema
        )

        assert response == sentinel.second_call
        base_client._get_refreshed_token.assert_called_once_with(
            base_client._oauth2_token.refresh_token
        )
        base_client._validated_response.assert_has_calls(
            [
                # It would be good to assert this call has the old header, but as
                # the object is mutated, you can't easily
                call(AnyRequest(), Schema),
                call(
                    AnyRequest.containing_headers(
                        {"Authorization": "Bearer new_access_token"}
                    ),
                    Schema,
                ),
            ]
        )

    @pytest.mark.usefixtures("access_token_no_refresh")
    def test_it_raises_CanvasAPIAccessTokenError_if_refresh_token_is_None(
        self, base_client, Schema
    ):
        base_client._validated_response.side_effect = CanvasAPIAccessTokenError()

        with pytest.raises(CanvasAPIAccessTokenError):
            base_client.make_authenticated_request(
                method="method", path="path", schema=Schema
            )

    @pytest.fixture
    def access_token_no_refresh(self, db_session, access_token_fields):
        access_token = OAuth2Token(**dict(access_token_fields, refresh_token=None))
        db_session.add(access_token)
        return access_token

    @pytest.fixture
    def base_client(self, base_client):
        with mock.patch.object(base_client, "_get_refreshed_token"):
            with mock.patch.object(base_client, "_validated_response"):
                yield base_client


pytestmark = pytest.mark.usefixtures("ai_getter")


@pytest.fixture
def base_client(pyramid_request):
    return _CanvasAPIAuthenticatedClient(sentinel.context, pyramid_request)


@pytest.fixture(autouse=True)
def http_session(patch):
    session = patch("lms.services.canvas_api.Session")

    return session()


@pytest.fixture(autouse=True)
def application_instance(db_session, pyramid_request):
    """Return the ApplicationInstance that the test OAuth2Token's belong to."""
    application_instance = ApplicationInstance(
        consumer_key=pyramid_request.lti_user.oauth_consumer_key,
        shared_secret="test_shared_secret",
        lms_url="test_lms_url",
        requesters_email="test_requesters_email",
    )
    db_session.add(application_instance)
    return application_instance


@pytest.fixture
def access_token_fields(pyramid_request):
    return {
        "user_id": pyramid_request.lti_user.user_id,
        "consumer_key": pyramid_request.lti_user.oauth_consumer_key,
        "access_token": "existing_access_token",
        "refresh_token": "existing_refresh_token",
        "expires_in": 9999,
    }


@pytest.fixture
def access_token(db_session, access_token_fields):
    access_token = OAuth2Token(**access_token_fields)
    db_session.add(access_token)
    return access_token


@pytest.fixture
def Schema():
    # pylint: disable=invalid-name
    Schema = create_autospec(RequestsResponseSchema)
    Schema.many = False

    return Schema


@pytest.fixture
def PaginatedSchema(Schema):
    Schema.many = True

    Schema.return_value.parse.side_effect = (
        [f"item_{i}"] for i in range(100)
    )  # pragma: no cover

    return Schema
