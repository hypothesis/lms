from unittest.mock import call, sentinel

import pytest
from h_matchers import Any

from lms.models import CanvasFile
from lms.services import (
    CanvasAPIAccessTokenError,
    CanvasAPIError,
    CanvasAPIServerError,
    CanvasFileNotFoundInCourse,
)
from lms.services.canvas_api.client import CanvasAPIClient
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "http_session", "oauth_token", "canvas_files_service"
)


class TestGetToken:
    def test_it(self, canvas_api_client, authenticated_client):
        token = canvas_api_client.get_token(sentinel.authorization_code)

        authenticated_client.get_token.assert_called_once_with(
            sentinel.authorization_code
        )
        assert token == authenticated_client.get_token.return_value

    @pytest.fixture
    def authenticated_client(self, patch):
        return patch("lms.services.canvas_api._authenticated.AuthenticatedClient")


class TestAuthenticatedUsersSections:
    def test_it(self, canvas_api_client, http_session):
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

    def test_it_deduplicates_sections(self, canvas_api_client, http_session):
        http_session.set_response(
            {"sections": [{"id": 1, "name": "name"}, {"id": 1, "name": "name"}]}
        )

        sections = canvas_api_client.authenticated_users_sections("course_id")

        assert sections == [{"id": 1, "name": "name"}]

    def test_it_raises_CanvasAPIError_with_conflicting_duplicates(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            {"sections": [{"id": 1, "name": "name"}, {"id": 1, "name": "DIFFERENT"}]}
        )

        with pytest.raises(CanvasAPIError):
            canvas_api_client.authenticated_users_sections("course_id")


class TestCourseSections:
    def test_it(self, canvas_api_client, http_session):
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

    def test_it_deduplicates_sections(self, canvas_api_client, http_session):
        http_session.set_response(
            [{"id": 1, "name": "name"}, {"id": 1, "name": "name"}]
        )

        sections = canvas_api_client.course_sections("course_id")

        assert sections == [{"id": 1, "name": "name"}]

    def test_it_raises_CanvasAPIError_with_conflicting_duplicates(
        self, canvas_api_client, http_session
    ):
        http_session.set_response(
            [{"id": 1, "name": "name"}, {"id": 1, "name": "DIFFERENT"}]
        )

        with pytest.raises(CanvasAPIError):
            canvas_api_client.course_sections("course_id")

    def test_it_raises_CanvasAPIError_with_too_few_returned(
        self, canvas_api_client, http_session
    ):
        http_session.set_response([])

        with pytest.raises(CanvasAPIError):
            canvas_api_client.course_sections("dummy")


class TestUsersSections:
    def test_it(self, canvas_api_client, http_session):
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

    def test_it_deduplicates_sections(self, canvas_api_client, http_session):
        http_session.set_response(
            {"enrollments": [{"course_section_id": 1}, {"course_section_id": 1}]}
        )

        sections = canvas_api_client.users_sections("user_id", "course_id")

        assert sections == [{"id": 1}]


class TestListFiles:
    def test_it(
        self, canvas_api_client, canvas_files_service, http_session, pyramid_request
    ):
        files = [
            {
                "display_name": "display_name_1",
                "filename": "filename_1",
                "id": 1,
                "updated_at": "updated_at_1",
                "size": 1024,
            },
            {
                "display_name": "display_name_2",
                "filename": "filename_2",
                "id": 2,
                "updated_at": "updated_at_2",
                "size": 1024,
            },
        ]
        files_with_noise = [dict(file, unexpected="ignored") for file in files]
        http_session.set_response(files_with_noise)

        response = canvas_api_client.list_files("COURSE_ID")

        # It gets the files from the Canvas API
        http_session.send.assert_called_once_with(
            Any.request(
                "GET",
                url=Any.url.with_path("api/v1/courses/COURSE_ID/files").with_query(
                    {"content_types[]": "application/pdf", "per_page": Any.string()}
                ),
            ),
            timeout=Any(),
        )

        # It upserts the files into the DB.
        assert canvas_files_service.upsert.call_args_list == [
            call(
                Any.instance_of(CanvasFile).with_attrs(
                    {
                        "consumer_key": pyramid_request.lti_user.oauth_consumer_key,
                        "tool_consumer_instance_guid": pyramid_request.lti_user.tool_consumer_instance_guid,
                        "course_id": "COURSE_ID",
                        "file_id": file_dict["id"],
                        "filename": file_dict["filename"],
                        "size": file_dict["size"],
                    }
                )
            )
            for file_dict in files
        ]

        # It returns the files.
        assert response == files


class TestCheckFileInCourse:
    @pytest.mark.parametrize("file_id", [1, "1"])
    def test_it_checks_that_the_file_is_in_the_course(
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

    def test_it_raises_if_the_file_isnt_in_the_course(self, canvas_api_client):
        with pytest.raises(CanvasFileNotFoundInCourse):
            canvas_api_client.check_file_in_course(
                file_id="not_in_course", course_id="test_course_id"
            )

    @pytest.fixture(autouse=True)
    def list_files_response(self, http_session):
        """Make the network send a valid Canvas API list files response."""
        http_session.send.return_value = factories.requests.Response(
            json_data=[
                {
                    "display_name": "display_name_1",
                    "filename": "filename_1",
                    "id": 1,
                    "updated_at": "updated_at_1",
                    "size": 1024,
                },
                {
                    "display_name": "display_name_2",
                    "filename": "filename_2",
                    "id": 2,
                    "updated_at": "updated_at_2",
                    "size": 1024,
                },
            ],
            status_code=200,
        )


class TestPublicURL:
    def test_it(self, canvas_api_client, http_session):
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
    def test_methods_require_access_token(self, data_method, oauth2_token_service):
        oauth2_token_service.get.side_effect = CanvasAPIAccessTokenError(
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
def canvas_api_client(authenticated_client, canvas_files_service, pyramid_request):
    return CanvasAPIClient(
        authenticated_client, canvas_files_service, pyramid_request.lti_user
    )
