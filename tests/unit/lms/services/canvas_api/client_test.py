from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.services import CanvasAPIError, CanvasAPIServerError, OAuth2TokenError
from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api.client import CanvasAPIClient
from tests import factories


class TestCanvasAPIClient:
    def test_get_token(self, canvas_api_client, authenticated_client):
        token = canvas_api_client.get_token(sentinel.authorization_code)

        authenticated_client.get_token.assert_called_once_with(
            sentinel.authorization_code
        )
        assert token == authenticated_client.get_token.return_value

    def test_get_refreshed_token(self, canvas_api_client, authenticated_client):
        refreshed_token = canvas_api_client.get_refreshed_token(sentinel.refresh_token)

        authenticated_client.get_refreshed_token.assert_called_once_with(
            sentinel.refresh_token
        )
        assert refreshed_token == authenticated_client.get_refreshed_token.return_value

    @pytest.fixture
    def authenticated_client(self):
        return create_autospec(AuthenticatedClient, instance=True, spec_set=True)


@pytest.mark.usefixtures("http_session", "oauth_token")
class TestCanvasAPIClientIntegrated:
    """
    Integrated tests for CanvasAPIClient.

    Tests for CanvasAPIClient in integration with real (not mocked) instances
    of AuthenticatedClient and BasicClient.
    """

    def test_pages(self, canvas_api_client):
        assert canvas_api_client.pages == sentinel.pages_client

    def test_authenticated_users_sections(self, canvas_api_client, http_session):
        sections = [{"id": 1, "name": "name_1"}, {"id": 2, "name": "name_2"}]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data={"sections": sections}
        )

        response = canvas_api_client.authenticated_users_sections("COURSE_ID")

        assert response == sections
        self.assert_session_send(
            http_session, "api/v1/courses/COURSE_ID", query={"include[]": "sections"}
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
        self.assert_session_send(
            http_session,
            "api/v1/courses/COURSE_ID/sections",
            query={"per_page": Any.string()},
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
        self.assert_session_send(
            http_session,
            "api/v1/courses/COURSE_ID/group_categories",
            query={"per_page": Any.string()},
        )

    @pytest.mark.parametrize(
        "only_own_groups,include_users", [(True, False), (False, True)]
    )
    def test_course_groups(
        self, only_own_groups, include_users, canvas_api_client, http_session
    ):
        groups = [
            {
                "id": 1,
                "name": "Group 1",
                "description": "Group 1",
                "group_category_id": 1,
                "course_id": 1,
            },
            {
                "id": 2,
                "name": "Group 2",
                "description": "Group 2",
                "group_category_id": 1,
                "course_id": 1,
            },
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=groups
        )

        response = canvas_api_client.course_groups(
            "COURSE_ID", only_own_groups=only_own_groups, include_users=include_users
        )

        assert response == groups

        expected_params = {
            "per_page": Any.string(),
            "only_own_groups": str(only_own_groups),
        }
        expected_timeout = Any()

        if include_users:
            expected_params["include[]"] = "users"
            expected_timeout = (31, 31)  # pylint:disable=redefined-variable-type

        self.assert_session_send(
            http_session,
            "api/v1/courses/COURSE_ID/groups",
            query=expected_params,
            timeout=expected_timeout,
        )

    @pytest.mark.parametrize("group_category_id", (1, "1"))
    @pytest.mark.usefixtures("list_groups_response")
    def test_current_user_groups(self, canvas_api_client, group_category_id):
        course_id = 1

        response = canvas_api_client.current_user_groups(course_id, group_category_id)

        assert len(response) == 1
        assert response[0]["group_category_id"] == int(group_category_id)

    @pytest.mark.usefixtures("list_groups_response")
    def test_current_user_groups_no_group_category(self, canvas_api_client):
        course_id = 1

        response = canvas_api_client.current_user_groups(
            course_id, group_category_id=None
        )

        assert len(response) == 2

    @pytest.mark.usefixtures("list_groups_response")
    def test_current_user_groups_empty(self, canvas_api_client):
        course_id = 1
        group_category_id = 10000

        response = canvas_api_client.current_user_groups(course_id, group_category_id)

        assert not response

    @pytest.mark.usefixtures("list_groups_with_users_response")
    def test_user_groups_none_match_group_category_id(self, canvas_api_client):
        course_id = 1
        user_id = 10000
        group_category_id = 10000

        response = canvas_api_client.user_groups(course_id, user_id, group_category_id)

        assert not response

    @pytest.mark.usefixtures("list_groups_with_users_response")
    def test_user_groups_none_match_user_id(self, canvas_api_client):
        course_id = 1
        user_id = 10000
        group_category_id = 2

        response = canvas_api_client.user_groups(course_id, user_id, group_category_id)

        assert not response

    @pytest.mark.usefixtures("list_groups_with_users_response")
    def test_user_groups_no_group_category(self, canvas_api_client):
        course_id = 1
        user_id = 1

        response = canvas_api_client.user_groups(course_id, user_id)

        assert len(response) == 1
        assert user_id in [u["id"] for u in response[0]["users"]]

    @pytest.mark.usefixtures("list_groups_response")
    def test_user_groups_no_users_in_response(self, canvas_api_client):
        user_id = course_id = 1
        group_category_id = 2

        response = canvas_api_client.user_groups(course_id, user_id, group_category_id)

        assert not response

    @pytest.mark.parametrize("group_category_id", (2, "2"))
    @pytest.mark.parametrize("user_id", (1, "1"))
    @pytest.mark.usefixtures("list_groups_with_users_response")
    def test_user_groups(self, canvas_api_client, user_id, group_category_id):
        course_id = 1

        response = canvas_api_client.user_groups(course_id, user_id, group_category_id)

        assert len(response) == 1
        assert int(user_id) in [u["id"] for u in response[0]["users"]]
        assert response[0]["group_category_id"] == int(group_category_id)

    @pytest.mark.usefixtures("list_groups_response")
    @pytest.mark.parametrize("course_id", (1, "1"))
    def test_group_category_groups(self, canvas_api_client, http_session, course_id):
        response = canvas_api_client.group_category_groups(course_id, "GROUP_CATEGORY")

        assert len(response) == 2
        self.assert_session_send(
            http_session,
            "api/v1/group_categories/GROUP_CATEGORY/groups",
            query={"per_page": Any.string()},
        )

    @pytest.mark.usefixtures("list_groups_response")
    def test_group_category_groups_from_another_course(self, canvas_api_client):
        with pytest.raises(CanvasAPIError) as exc_info:
            canvas_api_client.group_category_groups(2, "GROUP_CATEGORY")

        assert (
            exc_info.value.message
            == "Group set GROUP_CATEGORY doesn't belong to course 2"
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
        self.assert_session_send(
            http_session,
            "api/v1/courses/COURSE_ID/users/USER_ID",
            query={"include[]": "enrollments"},
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

    def test_list_files(
        self, canvas_api_client, http_session, file_service, list_files_json
    ):
        files_with_noise = [
            dict(file, unexpected="ignored") for file in list_files_json
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=files_with_noise
        )

        response = canvas_api_client.list_files("COURSE_ID")

        assert response == [
            {
                "updated_at": file["updated_at"],
                "lms_id": file["id"],
                "folder_id": file["folder_id"],
                "display_name": file["display_name"],
                "size": file["size"],
                "id": f'canvas://file/course/COURSE_ID/file_id/{file["id"]}',
                "mime_type": "application/pdf",
            }
            for file in list_files_json
        ]
        self.assert_session_send(
            http_session,
            "api/v1/courses/COURSE_ID/files",
            query={
                "content_types[]": "application/pdf",
                "per_page": Any.string(),
                "sort": "position",
            },
        )
        file_service.upsert.assert_called_once_with(
            [
                {
                    "type": "canvas_file",
                    "course_id": "COURSE_ID",
                    "lms_id": file["id"],
                    "name": file["display_name"],
                    "size": file["size"],
                    "parent_lms_id": file["folder_id"],
                }
                for file in list_files_json
            ]
        )

    def test_list_duplicate_files(self, canvas_api_client, http_session):
        files = [
            {
                "display_name": "display_name_1",
                "id": 1,
                "updated_at": "updated_at_1",
                "size": 12345,
                "folder_id": 100,
            },
            {
                "display_name": "display_name_1",
                "id": 1,
                "updated_at": "updated_at_1",
                "size": 12345,
                "folder_id": 100,
            },
        ]
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data=files
        )

        response = canvas_api_client.list_files("COURSE_ID")

        expected_file = files[0].copy()
        expected_file.update(
            {
                "mime_type": "application/pdf",
                "lms_id": 1,
                "id": "canvas://file/course/COURSE_ID/file_id/1",
            }
        )
        assert response == [expected_file]

    def test_list_files_with_folders(
        self,
        canvas_api_client,
        http_session,
        file_service,
        list_files_json,
        list_folders_json,
    ):
        canvas_api_client._folders_enabled = True  # noqa: SLF001
        http_session.send.side_effect = [
            factories.requests.Response(status_code=200, json_data=list_files_json),
            factories.requests.Response(status_code=200, json_data=list_folders_json),
        ]

        response = canvas_api_client.list_files("COURSE_ID")

        http_session.send.assert_called_with(
            Any.request(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/folders").with_query(
                    {"per_page": Any.string()}
                ),
            ),
            timeout=Any(),
        )

        file_service.upsert.assert_called_with(
            [
                {
                    "type": "canvas_folder",
                    "course_id": "COURSE_ID",
                    "lms_id": folder["id"],
                    "name": folder["name"],
                    "parent_lms_id": folder["parent_folder_id"],
                }
                for folder in list_folders_json
            ]
        )
        assert response == [
            {
                "display_name": "File at root",
                "size": 12345,
                "lms_id": 1,
                "folder_id": 100,
                "updated_at": "updated_at_1",
                "type": "File",
                "mime_type": "application/pdf",
                "id": "canvas://file/course/COURSE_ID/file_id/1",
            },
            {
                "id": 200,
                "display_name": "folder",
                "folder_id": 100,
                "updated_at": "updated_at_1",
                "type": "Folder",
                "children": [
                    {
                        "display_name": "File in folder",
                        "size": 12345,
                        "lms_id": 2,
                        "folder_id": 200,
                        "updated_at": "updated_at_2",
                        "type": "File",
                        "mime_type": "application/pdf",
                        "id": "canvas://file/course/COURSE_ID/file_id/2",
                    },
                    {
                        "id": 300,
                        "display_name": "folder nested",
                        "folder_id": 200,
                        "updated_at": "updated_at_1",
                        "type": "Folder",
                        "children": [
                            {
                                "display_name": "File in folder nested",
                                "size": 12345,
                                "lms_id": 3,
                                "folder_id": 300,
                                "updated_at": "updated_at_3",
                                "type": "File",
                                "mime_type": "application/pdf",
                                "id": "canvas://file/course/COURSE_ID/file_id/3",
                            }
                        ],
                    },
                ],
            },
        ]

    def test_public_url(self, canvas_api_client, http_session):
        http_session.send.return_value = factories.requests.Response(
            status_code=200, json_data={"public_url": "public_url_value"}
        )

        response = canvas_api_client.public_url("FILE_ID")

        assert response == "public_url_value"
        self.assert_session_send(http_session, "api/v1/files/FILE_ID/public_url")

    def test_methods_require_access_token(self, data_method, oauth2_token_service):
        oauth2_token_service.get.side_effect = OAuth2TokenError(
            "We don't have a Canvas API access token for this user"
        )

        with pytest.raises(OAuth2TokenError):
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

    @pytest.fixture
    def list_files_json(self):
        return [
            {
                "display_name": "File at root",
                "id": 1,
                "updated_at": "updated_at_1",
                "size": 12345,
                "folder_id": 100,
            },
            {
                "display_name": "File in folder",
                "id": 2,
                "updated_at": "updated_at_2",
                "size": 12345,
                "folder_id": 200,
            },
            {
                "display_name": "File in folder nested",
                "id": 3,
                "updated_at": "updated_at_3",
                "size": 12345,
                "folder_id": 300,
            },
        ]

    @pytest.fixture
    def list_folders_json(self):
        return [
            {
                "name": "root folder",
                "id": 100,
                "updated_at": "updated_at_1",
                "parent_folder_id": None,
            },
            {
                "name": "folder",
                "id": 200,
                "updated_at": "updated_at_1",
                "parent_folder_id": 100,
            },
            {
                "name": "folder nested",
                "id": 300,
                "updated_at": "updated_at_1",
                "parent_folder_id": 200,
            },
        ]

    @pytest.fixture
    def list_groups_response(self, http_session):
        http_session.send.return_value = factories.requests.Response(
            json_data=[
                {
                    "id": 1,
                    "name": "Group 1",
                    "description": "Group 1",
                    "group_category_id": 1,
                    "course_id": 1,
                },
                {
                    "id": 2,
                    "name": "Group 2",
                    "description": "Group 2",
                    "group_category_id": 2,
                    "course_id": 1,
                },
            ],
            status_code=200,
        )

    @pytest.fixture
    def list_groups_with_users_response(self, http_session):
        http_session.send.return_value = factories.requests.Response(
            json_data=[
                {
                    "id": 1,
                    "name": "Group 1",
                    "description": "Group 1",
                    "group_category_id": 1,
                    "users": [],
                    "course_id": 1,
                },
                {
                    "id": 2,
                    "name": "Group 2",
                    "description": "Group 2",
                    "group_category_id": 2,
                    "users": [{"id": 1}],
                    "course_id": 1,
                },
            ],
            status_code=200,
        )

    @pytest.fixture(params=tuple(methods.items()), ids=tuple(methods.keys()))
    def data_method(self, request, canvas_api_client):
        method, args = request.param

        return lambda: getattr(canvas_api_client, method)(*args)

    def assert_session_send(
        self, http_session, path, method="GET", query=None, timeout=(10, 10)
    ):
        http_session.send.assert_called_once_with(
            Any.request(method, url=Any.url.with_path(path).with_query(query)),
            timeout=timeout,
        )


@pytest.fixture
def canvas_api_client(authenticated_client, file_service):
    return CanvasAPIClient(
        authenticated_client, file_service, pages_client=sentinel.pages_client
    )
