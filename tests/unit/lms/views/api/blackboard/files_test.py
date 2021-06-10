from unittest.mock import sentinel

import pytest

from lms.views.api.blackboard.files import BlackboardFilesAPIViews

pytestmark = pytest.mark.usefixtures("oauth2_token_service", "blackboard_api_client")


class TestListFiles:
    def test_it(self, views, pyramid_request, blackboard_api_client):
        pyramid_request.matchdict["course_id"] = "TEST_COURSE_ID"

        files = views.list_files()

        blackboard_api_client.list_files.assert_called_once_with("TEST_COURSE_ID")
        assert files == blackboard_api_client.list_files.return_value


class TestViaURL:
    def test_it_returns_the_Via_URL_for_the_selected_hardcoded_PDF_URL(
        self, helpers, pyramid_request, view, blackboard_api_client
    ):
        response = view()

        blackboard_api_client.public_url.assert_called_once_with(
            sentinel.course_id, sentinel.document_url
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            blackboard_api_client.public_url.return_value,
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = sentinel.course_id
        pyramid_request.params["document_url"] = sentinel.document_url
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
