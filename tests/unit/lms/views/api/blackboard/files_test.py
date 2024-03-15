import pytest

from lms.views.api.blackboard.files import BlackboardFilesAPIViews, FileNotFoundInCourse

pytestmark = pytest.mark.usefixtures(
    "oauth2_token_service", "blackboard_api_client", "course_copy_plugin"
)


class TestListFiles:
    def test_it_returns_the_courses_top_level_contents(
        self, view, blackboard_api_client, pyramid_request
    ):
        files = view()

        blackboard_api_client.list_files.assert_called_once_with("COURSE_ID", None)
        assert files == [
            {
                "id": "blackboard://content-resource/_7851_0/",
                "updated_at": "2008-05-06T07:26:35.000z",
                "display_name": "File_1.pdf",
                "type": "File",
                "mime_type": "application/pdf",
                "parent_id": None,
            },
            {
                "id": "_7851_1",
                "updated_at": "1983-05-26T02:37:23.000z",
                "display_name": "Folder_1",
                "type": "Folder",
                "parent_id": None,
                "contents": {
                    "authUrl": pyramid_request.route_url(
                        "blackboard_api.oauth.authorize"
                    ),
                    "path": pyramid_request.route_path(
                        "blackboard_api.courses.folders.files.list",
                        course_id="COURSE_ID",
                        folder_id="_7851_1",
                    ),
                },
            },
        ]

    def test_if_given_a_folder_id_it_returns_the_folders_contents(
        self, view, blackboard_api_client, pyramid_request
    ):
        pyramid_request.matchdict["folder_id"] = "FOLDER_ID"

        files = view()

        blackboard_api_client.list_files.assert_called_once_with(
            "COURSE_ID", "FOLDER_ID"
        )
        for file in files:
            assert file["parent_id"] == "FOLDER_ID"

    @pytest.fixture
    def blackboard_api_client(self, blackboard_api_client):
        blackboard_api_client.list_files.return_value = [
            {
                "id": "_7851_0",
                "modified": "2008-05-06T07:26:35.000z",
                "name": "File_1.pdf",
                "mimeType": "application/pdf",
                "type": "File",
            },
            {
                "id": "_7851_1",
                "modified": "1983-05-26T02:37:23.000z",
                "name": "Folder_1",
                "type": "Folder",
            },
            {
                "id": "_7851_2",
                "modified": "1980-05-26T02:37:23.000z",
                "name": "NOT_A_PDF.jpeg",
                "mimeType": "image/jpeg",
                "type": "File",
            },
        ]
        return blackboard_api_client

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        return pyramid_request

    @pytest.fixture
    def view(self, views):
        return views.list_files


class TestViaURL:
    @pytest.mark.parametrize("is_instructor", [True, False])
    def test_it(
        self,
        view,
        blackboard_api_client,
        helpers,
        pyramid_request,
        course_service,
        course_copy_plugin,
        is_instructor,
        request,
    ):
        if is_instructor:
            request.getfixturevalue("user_is_instructor")
        course_copy_plugin.is_file_in_course.return_value = True

        response = view()

        course_service.get_by_context_id.assert_called_once_with(
            "COURSE_ID", raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        course.get_mapped_file_id.assert_called_once_with("FILE_ID")
        file_id = course.get_mapped_file_id.return_value

        if is_instructor:
            course_copy_plugin.is_file_in_course.assert_called_once_with(
                "COURSE_ID", file_id
            )

        blackboard_api_client.public_url.assert_called_once_with(
            "COURSE_ID", course.get_mapped_file_id.return_value
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            blackboard_api_client.public_url.return_value,
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_when_file_not_in_course_fixed_by_course_copy(
        self,
        view,
        blackboard_api_client,
        helpers,
        pyramid_request,
        course_service,
        course_copy_plugin,
    ):
        course_copy_plugin.is_file_in_course.return_value = False

        response = view()

        course_service.get_by_context_id.assert_called_once_with(
            "COURSE_ID", raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        course.get_mapped_file_id.assert_called_once_with("FILE_ID")
        file_id = course.get_mapped_file_id.return_value

        course_copy_plugin.is_file_in_course.assert_called_once_with(
            "COURSE_ID", file_id
        )
        course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
            file_id, "COURSE_ID"
        )
        found_file = course_copy_plugin.find_matching_file_in_course.return_value
        blackboard_api_client.public_url.assert_called_once_with(
            "COURSE_ID", found_file.lms_id
        )
        course.set_mapped_file_id.assert_called_once_with(file_id, found_file.lms_id)

        helpers.via_url.assert_called_once_with(
            pyramid_request,
            blackboard_api_client.public_url.return_value,
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    @pytest.mark.usefixtures("user_is_instructor")
    def test_it_when_file_not_in_course(self, view, course_service, course_copy_plugin):
        course_copy_plugin.is_file_in_course.return_value = False
        course_copy_plugin.find_matching_file_in_course.return_value = None

        with pytest.raises(FileNotFoundInCourse) as exc_info:
            view()

        assert exc_info.value.error_code == "blackboard_file_not_found_in_course"

        course_service.get_by_context_id.assert_called_once_with(
            "COURSE_ID", raise_on_missing=True
        )
        course = course_service.get_by_context_id.return_value
        course.get_mapped_file_id.assert_called_once_with("FILE_ID")
        file_id = course.get_mapped_file_id.return_value

        course_copy_plugin.is_file_in_course.assert_called_once_with(
            "COURSE_ID", file_id
        )
        course_copy_plugin.find_matching_file_in_course.assert_called_once_with(
            file_id, "COURSE_ID"
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        pyramid_request.params["document_url"] = (
            "blackboard://content-resource/FILE_ID/"
        )
        return pyramid_request

    @pytest.fixture
    def view(self, views):
        return views.via_url


@pytest.fixture(autouse=True)
def helpers(patch):
    return patch("lms.views.api.blackboard.files.helpers")


@pytest.fixture
def views(pyramid_request):
    return BlackboardFilesAPIViews(pyramid_request)
