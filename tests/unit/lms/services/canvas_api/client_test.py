from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.services import CanvasAPIAccessTokenError, CanvasAPIError, CanvasAPIServerError
from lms.services.canvas_api.client import CanvasAPIClient


class TestCanvasAPIClientGetToken:
    # This is the only test where we fake out the underlying class, because
    # this _one_ call is just a pass through.

    def test_get_token(self, canvas_api_client, authenticated_client):
        token = canvas_api_client.get_token(sentinel.authorization_code)

        authenticated_client.get_token.assert_called_once_with(
            sentinel.authorization_code
        )
        assert token == authenticated_client.get_token.return_value

    @pytest.fixture
    def authenticated_client(self, patch):
        return patch("lms.services.canvas_api._authenticated.AuthenticatedClient")


@pytest.mark.usefixtures("http_session", "oauth_token")
class TestCanvasAPIClient:
    def test_authenticated_users_sections(self, canvas_api_client, http_session):
        sections = [{"id": 1, "name": "name_1"}, {"id": 2, "name": "name_2"}]
        http_session.set_response({"sections": sections})

        response = canvas_api_client.authenticated_users_sections("COURSE_ID")

        assert response == sections
        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID").with_query(
                    {"include[]": "sections"}
                ),
            ),
            timeout=Any(),
        )

    def test_authenticated_users_sections_deduplicates_sections(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            {"sections": [{"id": 1, "name": "name"}, {"id": 1, "name": "name"}]}
        )

        sections = canvas_api_client.authenticated_users_sections("course_id")

        assert sections == [{"id": 1, "name": "name"}]

    def test_authenticated_users_sections_raises_CanvasAPIError_with_conflicting_duplicates(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            {"sections": [{"id": 1, "name": "name"}, {"id": 1, "name": "DIFFERENT"}]}
        )

        with pytest.raises(CanvasAPIError):
            canvas_api_client.authenticated_users_sections("course_id")

    def test_course_sections(self, canvas_api_client, http_session):
        sections = [
            {"id": 101, "name": "name_1"},
            {"id": 102, "name": "name_2"},
        ]
        sections_with_noise = [
            dict(section, unexpected="ignored") for section in sections
        ]

        http_session.set_response(sections_with_noise)

        response = canvas_api_client.course_sections("COURSE_ID")

        assert response == sections
        http_session.send.assert_called_once_with(
            Any.request(
                "GET", url=Any.url.with_path("api/v1/courses/COURSE_ID/sections")
            ),
            timeout=Any(),
        )

    def test_course_sections_deduplicates_sections(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            [{"id": 1, "name": "name"}, {"id": 1, "name": "name"}]
        )

        sections = canvas_api_client.course_sections("course_id")

        assert sections == [{"id": 1, "name": "name"}]

    def test_course_sections_raises_CanvasAPIError_with_conflicting_duplicates(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            [{"id": 1, "name": "name"}, {"id": 1, "name": "DIFFERENT"}]
        )

        with pytest.raises(CanvasAPIError):
            canvas_api_client.course_sections("course_id")

    def test_course_sections_raises_CanvasAPIError_with_too_few_returned(
        self, canvas_api_client, http_session
    ):
        http_session.set_response([])

        with pytest.raises(CanvasAPIError):
            canvas_api_client.course_sections("dummy")

    def test_users_sections(self, canvas_api_client, http_session):
        http_session.set_response(
            {
                "enrollments": [
                    {"course_section_id": 101, "unexpected": "ignored"},
                    {"course_section_id": 102, "unexpected": "ignored"},
                ]
            }
        )

        response = canvas_api_client.users_sections("USER_ID", "COURSE_ID")

        assert response == [{"id": 101}, {"id": 102}]
        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path(
                    "api/v1/courses/COURSE_ID/users/USER_ID"
                ).with_query({"include[]": "enrollments"}),
            ),
            timeout=Any(),
        )

    def test_users_sections_deduplicates_sections(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            {"enrollments": [{"course_section_id": 1}, {"course_section_id": 1}]}
        )

        sections = canvas_api_client.users_sections("user_id", "course_id")

        assert sections == [{"id": 1}]

    def test_list_files(self, canvas_api_client, http_session):
        files = [
            {"display_name": "display_name_1", "id": 1, "updated_at": "updated_at_1"},
            {"display_name": "display_name_1", "id": 1, "updated_at": "updated_at_1"},
        ]
        files_with_noise = [dict(file, unexpected="ignored") for file in files]
        http_session.set_response(files_with_noise)

        response = canvas_api_client.list_files("COURSE_ID")

        assert response == files

        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/files").with_query(
                    {"content_types[]": "application/pdf", "per_page": Any.string()}
                ),
            ),
            timeout=Any(),
        )

    def test_public_url(self, canvas_api_client, http_session):
        http_session.set_response({"public_url": "public_url_value"})

        response = canvas_api_client.public_url("FILE_ID")

        assert response == "public_url_value"
        http_session.send.assert_called_once_with(
            Any.request(
                "GET", url=Any.url.with_path("api/v1/files/FILE_ID/public_url")
            ),
            timeout=Any(),
        )


class TestMetaBehavior:
    def test_methods_require_access_token(self, data_method, token_store):
        token_store.get.side_effect = CanvasAPIAccessTokenError(
            "We don't have a Canvas API access token for this user"
        )

        with pytest.raises(CanvasAPIAccessTokenError):
            data_method()

    @pytest.mark.usefixtures("oauth_token")
    def test_methods_raise_CanvasAPIServerError_if_the_response_json_has_the_wrong_format(
        self, data_method, http_session
    ):
        http_session.set_response({})

        with pytest.raises(CanvasAPIServerError):
            data_method()

    @pytest.mark.usefixtures("oauth_token")
    def test_methods_raise_CanvasAPIServerError_if_the_response_is_invalid_json(
        self, data_method, http_session
    ):
        http_session.set_response(raw="[broken json")

        with pytest.raises(CanvasAPIServerError):
            data_method()

    methods = {
        "authenticated_users_sections": ["course_id"],
        "course_sections": ["course_id"],
        "users_sections": ["user_id", "course_id"],
        "list_files": ["course_id"],
        "public_url": ["file_id"],
    }

    @pytest.fixture(params=tuple(methods.items()), ids=tuple(methods.keys()))
    def data_method(self, request, canvas_api_client):
        method, args = request.param

        return lambda: getattr(canvas_api_client, method)(*args)


@pytest.fixture
def canvas_api_client(authenticated_client):
    return CanvasAPIClient(authenticated_client)
