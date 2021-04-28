import pytest

from lms.views.admin import AdminViews

# from tests.unit.matchers import temporary_redirect_to


@pytest.mark.usefixtures("pyramid_config")
class TestAdminViews:
    def test_index(self, pyramid_request, views):
        pyramid_request.headers["Cookie"] = "session=session_value"

        response = views.index()

        assert response == {"session": "session_value"}

    def test_logged_out_redirects_to_login(self, pyramid_request, views):
        response = views.logged_out()

        assert response.status_code == 302
        assert response.location == pyramid_request.route_url(
            "pyramid_googleauth.login"
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminViews(pyramid_request)
