import pytest

from lms.views.api.blackboard.files import BlackboardFilesAPIViews

pytestmark = pytest.mark.usefixtures("oauth2_token_service", "blackboard_api_client")


class TestListFiles:
    def test_it(self, view, blackboard_api_client):
        blackboard_api_client.list_files.return_value = [
            {
                "id": "_7851_0",
                "modified": "2008-05-06T07:26:35.000z",
                "name": "File_0.pdf",
                "mimeType": "application/pdf",
            },
            {
                "id": "_7851_1",
                "modified": "1983-05-26T02:37:23.000z",
                "name": "File_1.pdf",
                "mimeType": "application/pdf",
            },
            {
                "id": "_7851_2",
                "modified": "1980-05-26T02:37:23.000z",
                "name": "NOT_A_PDF.jpeg",
                "mimeType": "image/jpeg",
            },
        ]

        files = view()

        blackboard_api_client.list_files.assert_called_once_with("COURSE_ID")
        assert files == [
            {
                "id": "blackboard://content-resource/_7851_0/",
                "updated_at": "2008-05-06T07:26:35.000z",
                "display_name": "File_0.pdf",
            },
            {
                "id": "blackboard://content-resource/_7851_1/",
                "updated_at": "1983-05-26T02:37:23.000z",
                "display_name": "File_1.pdf",
            },
        ]

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
