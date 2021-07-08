import pytest

from lms.views.api.blackboard.files import BlackboardFilesAPIViews

pytestmark = pytest.mark.usefixtures("oauth2_token_service", "blackboard_api_client")


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
    def test_it(self, view, blackboard_api_client, helpers, pyramid_request):
        response = view()

        blackboard_api_client.public_url.assert_called_once_with("COURSE_ID", "FILE_ID")
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            blackboard_api_client.public_url.return_value,
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        pyramid_request.params[
            "document_url"
        ] = "blackboard://content-resource/FILE_ID/"
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
