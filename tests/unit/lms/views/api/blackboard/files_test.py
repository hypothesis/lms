import pytest

from lms.services import NoOAuth2Token, ProxyAPIAccessTokenError
from lms.views.api.blackboard.files import BlackboardFilesAPIViews

pytestmark = pytest.mark.usefixtures("oauth2_token_service")


class CommonTests:
    def test_it_raises_ProxyAPIAccessTokenError_if_theres_no_access_token_for_the_user(
        self, oauth2_token_service, view
    ):
        oauth2_token_service.get.side_effect = NoOAuth2Token()

        with pytest.raises(ProxyAPIAccessTokenError):
            view()


class TestListFiles(CommonTests):
    def test_it_returns_a_hardcoded_list_of_files(self, view):
        assert view() == [
            {
                "id": "blackboard://content-resource/123",
                "display_name": "Fake Blackboard File 1",
                "updated_at": "2020-06-10T16:49:19Z",
            },
            {
                "id": "blackboard://content-resource/456",
                "display_name": "Fake Blackboard File 2",
                "updated_at": "2020-06-10T16:48:53Z",
            },
            {
                "id": "blackboard://content-resource/789",
                "display_name": "Fake Blackboard File 3",
                "updated_at": "2020-08-03T14:06:00Z",
            },
        ]

    @pytest.fixture
    def view(self, views):
        return views.list_files


class TestViaURL(CommonTests):
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
