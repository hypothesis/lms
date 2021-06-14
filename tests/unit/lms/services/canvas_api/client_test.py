from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.services import (
    CanvasAPIError,
    CanvasAPIServerError,
    CanvasFileNotFoundInCourse,
    ProxyAPIAccessTokenError,
)
from lms.services.canvas_api.client import CanvasAPIClient
from tests import factories


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
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data={"sections": sections}
        )

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
        http_session.send.return_value = factories.requests.Response(
            status_code=200,
            json_data={
                "sections": [{"id": 1, "name": "name"}, {"id": 1, "name": "name"}]
            },
        )
        sections = canvas_api_client.authenticated_users_sections("course_id")

        assert sections == [{"id": 1, "name": "name"}]

    def test_authenticated_users_sections_raises_CanvasAPIError_with_conflicting_duplicates(
        self, canvas_api_client, http_session
    ):
        http_session.send.return_value = factories.requests.Response(
            status_code=200,
            json_data={
                "sections": [{"id": 1, "name": "name"}, {"id": 1, "name": "DIFFERENT"}]
            },
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

        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=sections_with_noise
        )

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
        http_session.send.return_value = factories.requests.Response(
            status_code=200,
            json_data=[{"id": 1, "name": "name"}, {"id": 1, "name": "name"}],
        )

        sections = canvas_api_client.course_sections("course_id")

        assert sections == [{"id": 1, "name": "name"}]

    def test_course_sections_raises_CanvasAPIError_with_conflicting_duplicates(
        self, canvas_api_client, http_session
    ):
        http_session.send.return_value = factories.requests.Response(
            status_code=200,
            json_data=[{"id": 1, "name": "name"}, {"id": 1, "name": "DIFFERENT"}],
        )

        with pytest.raises(CanvasAPIError):
            canvas_api_client.course_sections("course_id")

    def test_course_sections_raises_CanvasAPIError_with_too_few_returned(
        self, canvas_api_client, http_session
    ):
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=[]
        )

        with pytest.raises(CanvasAPIError):
            canvas_api_client.course_sections("dummy")

    def test_group_categories_list(self, canvas_api_client, http_session):
        group_categories = [
            {"id": 1, "name": "Group category 1"},
            {"id": 2, "name": "Group category 2"},
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=group_categories
        )

        response = canvas_api_client.course_group_categories("COURSE_ID")

        assert response == group_categories

        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path(
                    "api/v1/courses/COURSE_ID/group_categories"
                ).with_query({"per_page": Any.string()}),
            ),
            timeout=Any(),
        )

    @pytest.mark.parametrize("only_own_groups", [True, False])
    def test_course_groups(self, only_own_groups, canvas_api_client, http_session):
        groups = [
            {
                "id": 1,
                "name": "Group 1",
                "description": "Group 1",
                "group_category_id": 1,
            },
            {
                "id": 2,
                "name": "Group 2",
                "description": "Group 2",
                "group_category_id": 1,
            },
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=groups
        )

        response = canvas_api_client.course_groups(
            "COURSE_ID", only_own_groups=only_own_groups
        )

        assert response == groups

        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/groups").with_query(
                    {"per_page": Any.string(), "only_own_groups": str(only_own_groups)}
                ),
            ),
            timeout=Any(),
        )

    def test_group_category_groups(self, canvas_api_client, http_session):
        groups = [
            {
                "id": 1,
                "name": "Group 1",
                "description": "Group 1",
                "group_category_id": 1,
            },
            {
                "id": 2,
                "name": "Group 2",
                "description": "Group 2",
                "group_category_id": 1,
            },
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=groups
        )

        response = canvas_api_client.group_category_groups("GROUP_CATEGORY")

        assert response == groups

        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path(
                    "api/v1/group_categories/GROUP_CATEGORY/groups"
                ).with_query({"per_page": Any.string()}),
            ),
            timeout=Any(),
        )

    def test_users_sections(self, canvas_api_client, http_session):
        http_session.send.return_value = factories.requests.Response(
            status_code=200,
            json_data={
                "enrollments": [
                    {"course_section_id": 101, "unexpected": "ignored"},
                    {"course_section_id": 102, "unexpected": "ignored"},
                ]
            },
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
        http_session.send.return_value = factories.requests.Response(
            status_code=200,
            json_data={
                "enrollments": [{"course_section_id": 1}, {"course_section_id": 1}]
            },
        )

        sections = canvas_api_client.users_sections("user_id", "course_id")

        assert sections == [{"id": 1}]

    def test_list_files(self, canvas_api_client, http_session):
        files = [
            {"display_name": "display_name_1", "id": 1, "updated_at": "updated_at_1"},
            {"display_name": "display_name_1", "id": 1, "updated_at": "updated_at_1"},
        ]
        files_with_noise = [dict(file, unexpected="ignored") for file in files]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=files_with_noise
        )

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

    @pytest.mark.usefixtures("list_files_response")
    @pytest.mark.parametrize("file_id", [1, "1"])
    def test_check_file_in_course_checks_that_the_file_is_in_the_course(
        self, canvas_api_client, file_id, http_session
    ):
        canvas_api_client.check_file_in_course(
            file_id=file_id, course_id="test_course_id"
        )

        http_session.send.assert_called_once_with(
            Any.request(
                url=Any.url.with_path("api/v1/courses/test_course_id/files"),
            ),
            timeout=Any(),
        )

    @pytest.mark.usefixtures("list_files_response")
    def test_check_file_in_course_raises_if_the_file_isnt_in_the_course(
        self, canvas_api_client
    ):
        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_api_client.check_file_in_course(
                file_id="not_in_course", course_id="test_course_id"
            )

    def test_public_url(self, canvas_api_client, http_session):
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data={"public_url": "public_url_value"}
        )

        response = canvas_api_client.public_url("FILE_ID")

        assert response == "public_url_value"
        http_session.send.assert_called_once_with(
            Any.request(
                "GET", url=Any.url.with_path("api/v1/files/FILE_ID/public_url")
            ),
            timeout=Any(),
        )

    @pytest.fixture
    def list_files_response(self, http_session):
        """Make the network send a valid Canvas API list files response."""
        http_session.send.return_value = factories.requests.Response(
            json_data=[
                {
                    "display_name": "display_name_1",
                    "id": 1,
                    "updated_at": "updated_at_1",
                },
                {
                    "display_name": "display_name_2",
                    "id": 2,
                    "updated_at": "updated_at_2",
                },
            ],
            status_code=200,
        )


class TestMetaBehavior:
    def test_methods_require_access_token(self, data_method, oauth2_token_service):
        oauth2_token_service.get.side_effect = ProxyAPIAccessTokenError(
            "We don't have a Canvas API access token for this user"
        )

        with pytest.raises(ProxyAPIAccessTokenError):
            data_method()

    @pytest.mark.usefixtures("oauth_token")
    def test_methods_raise_CanvasAPIServerError_if_the_response_json_has_the_wrong_format(
        self, data_method, http_session
    ):
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data={}
        )

        with pytest.raises(CanvasAPIServerError):
            data_method()

    @pytest.mark.usefixtures("oauth_token")
    def test_methods_raise_CanvasAPIServerError_if_the_response_is_invalid_json(
        self, data_method, http_session
    ):
        http_session.send.return_value = factories.requests.Response(
            status_code=200, raw="[broken json"
        )

        with pytest.raises(CanvasAPIServerError):
            data_method()

    methods = {
        "authenticated_users_sections": ["course_id"],
        "course_sections": ["course_id"],
        "course_group_categories": ["course_id"],
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
