from unittest.mock import Mock, sentinel

import pytest

from lms.views.admin import AdminViews, logged_out
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("pyramid_config", "application_instance_service")
class TestAdminViews:
    def test_index(self, pyramid_request):
        response = AdminViews(pyramid_request).index()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.installations")
        )

    @pytest.mark.parametrize("view_method,template_params", [("installations", {})])
    def test_template_views(self, view_method, template_params, views):
        response = getattr(views, view_method)()

        assert response == template_params

    def test_logged_out_redirects_to_login(self, pyramid_request):
        response = logged_out(pyramid_request)

        assert response.status_code == 302
        assert response.location == pyramid_request.route_url(
            "pyramid_googleauth.login"
        )

    def test_find_installation_no_query(self, pyramid_request):
        response = AdminViews(pyramid_request).find_installation()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.installations")
        )

    def test_find_installation_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.find.return_value = None
        pyramid_request.params["query"] = "some-value"
        response = AdminViews(pyramid_request).find_installation()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.installations")
        )

    def test_find_installation_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.find.return_value = Mock(id=1)
        pyramid_request.params["query"] = "some-value"
        response = AdminViews(pyramid_request).find_installation()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.installation", id=1)
        )

    def test_show_installation(self, pyramid_request, application_instance_service):
        application_instance_service.get.return_value = sentinel.installation
        pyramid_request.matchdict["id"] = "1"
        response = AdminViews(pyramid_request).show_installation()

        assert response == {"installation": sentinel.installation}

    def test_update_installation(self, pyramid_request, application_instance_service):
        application_instance_service.get.return_value = Mock(id=1)
        pyramid_request.matchdict["id"] = "1"
        response = AdminViews(pyramid_request).update_installation()

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.installation", id="1")
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminViews(pyramid_request)
