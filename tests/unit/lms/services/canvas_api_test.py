import json
from io import BytesIO
from unittest import mock
from unittest.mock import call, sentinel

import pytest
from _pytest.mark import param
from h_matchers import Any
from h_matchers.decorator import fluent_entrypoint
from h_matchers.matcher.core import Matcher
from requests import PreparedRequest, RequestException, Response

from lms.models import ApplicationInstance, OAuth2Token
from lms.services import CanvasAPIAccessTokenError, CanvasAPIError, CanvasAPIServerError
from lms.services.canvas_api import CanvasAPIClient
from lms.validation import ValidationError

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


def _make_response(json_data=None, raw=None, status_code=200):
    response = Response()

    if raw is None:
        raw = json.dumps(json_data)

    response.raw = BytesIO(raw.encode("utf-8"))
    response.status_code = status_code

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
        http_session.send.assert_called_once_with(
            AnyRequest(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/files").with_query(
                    {"content_types[]": "application/pdf", "per_page": "100"}
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
        self, api_client, http_session, db_session, pyramid_request, json_data
    ):
        http_session.send.return_value = _make_response(json_data)

        api_client.get_token("authorization_code")

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
                        "redirect_uri": api_client._redirect_uri,
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
        self, api_client, http_session, db_session, pyramid_request, json_data
    ):
        http_session.send.return_value = _make_response(json_data)

        api_client._get_refreshed_token("new_refresh_token")

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
        self, http_session, api_client, method, json_data
    ):
        http_session.send.return_value = _make_response(json_data)

        method = getattr(api_client, method)

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
    def test_it(self, api_client, http_session, schema):
        response = _make_response("request_body")
        http_session.send.return_value = response

        api_client._validated_response(sentinel.request, schema)

        http_session.send.assert_called_once_with(sentinel.request, timeout=9)
        schema.assert_called_once_with(response)
        schema.return_value.parse.assert_called_once_with()

    def test_it_raises_CanvasAPIError_for_request_errors(
        self, api_client, http_session, schema
    ):
        response = _make_response("request_body")
        response.raise_for_status = mock.MagicMock()
        response.raise_for_status.side_effect = RequestException
        http_session.send.return_value = response

        with pytest.raises(CanvasAPIError):
            api_client._validated_response(sentinel.request, schema)

    def test_it_raises_CanvasAPIError_for_validation_errors(self, api_client, schema):
        schema.return_value.parse.side_effect = ValidationError("Some error")

        with pytest.raises(CanvasAPIError):
            api_client._validated_response(sentinel.request, schema)

    @pytest.fixture
    def schema(self):
        return mock.MagicMock()


class TestMakeAuthenticatedRequest:
    def test_it(self, api_client, access_token):
        params = {"a": "1"}

        api_client.make_authenticated_request(
            method="method", path="path", schema=sentinel.schema, params=params
        )

        expected_url = (
            Any.url.matching(f"https://{api_client._canvas_url}")
            .with_path("api/v1/path")
            .with_query(params)
        )
        api_client._validated_response.assert_called_once_with(
            AnyRequest(method="METHOD", url=expected_url).containing_headers(
                {"Authorization": f"Bearer {access_token.access_token}"}
            ),
            sentinel.schema,
        )

    @pytest.mark.usefixtures("access_token")
    def test_it_refreshes_the_token_and_tries_again(self, api_client):
        api_client._validated_response.side_effect = [
            CanvasAPIAccessTokenError(),
            sentinel.second_call,
        ]
        api_client._get_refreshed_token.return_value = "new_access_token"

        response = api_client.make_authenticated_request(
            method="method", path="path", schema=sentinel.schema
        )

        assert response == sentinel.second_call
        api_client._get_refreshed_token.assert_called_once_with(
            api_client._oauth2_token.refresh_token
        )
        api_client._validated_response.assert_has_calls(
            [
                # It would be good to assert this call has the old header, but as
                # the object is mutated, you can't easily
                call(AnyRequest(), sentinel.schema),
                call(
                    AnyRequest.containing_headers(
                        {"Authorization": "Bearer new_access_token"}
                    ),
                    sentinel.schema,
                ),
            ]
        )

    @pytest.mark.usefixtures("access_token_no_refresh")
    def test_it_raises_CanvasAPIAccessTokenError_if_refresh_token_is_None(
        self, api_client
    ):
        api_client._validated_response.side_effect = CanvasAPIAccessTokenError()

        with pytest.raises(CanvasAPIAccessTokenError):
            api_client.make_authenticated_request(
                method="method", path="path", schema=sentinel.schema
            )

    @pytest.fixture
    def access_token_no_refresh(self, db_session, access_token_fields):
        access_token = OAuth2Token(**dict(access_token_fields, refresh_token=None))
        db_session.add(access_token)
        return access_token

    @pytest.fixture
    def api_client(self, api_client):
        with mock.patch.object(api_client, "_get_refreshed_token"):
            with mock.patch.object(api_client, "_validated_response"):
                yield api_client


pytestmark = pytest.mark.usefixtures("ai_getter")


@pytest.fixture
def api_client(pyramid_request):
    return CanvasAPIClient(sentinel.context, pyramid_request)


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
