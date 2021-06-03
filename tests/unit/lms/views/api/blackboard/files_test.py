import pytest

from lms.services import NoOAuth2Token, ProxyAPIAccessTokenError
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
        self, helpers, pyramid_request, view
    ):
        response = view()

        helpers.via_url.assert_called_once_with(
            pyramid_request,
            "https://h.readthedocs.io/_/downloads/client/en/latest/pdf/",
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_it_raises_ProxyAPIAccessTokenError_if_theres_no_access_token_for_the_user(
        self, oauth2_token_service, view
    ):
        oauth2_token_service.get.side_effect = NoOAuth2Token()

        with pytest.raises(ProxyAPIAccessTokenError):
            view()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["file_id"] = "456"
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
