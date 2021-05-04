from unittest.mock import Mock, sentinel

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound

from lms.views.admin import AdminViews, logged_out
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("pyramid_config", "application_instance_service")
class TestAdminViews:
    def test_index(self, pyramid_request):
        response = AdminViews(pyramid_request).index()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    @pytest.mark.parametrize("view_method,template_params", [("instances", {})])
    def test_template_views(self, view_method, template_params, views):
        response = getattr(views, view_method)()

        assert response == template_params

    def test_logged_out_redirects_to_login(self, pyramid_request):
        response = logged_out(pyramid_request)

        assert response.status_code == 302
        assert response.location == pyramid_request.route_url(
            "pyramid_googleauth.login"
        )

    def test_find_instance_no_query(self, pyramid_request):

        with pytest.raises(HTTPBadRequest):
            AdminViews(pyramid_request).find_instance()

    def test_find_instance_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get.return_value = None
        pyramid_request.params["query"] = "some-value"
        response = AdminViews(pyramid_request).find_instance()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_find_instance_found(self, pyramid_request, application_instance_service):
        application_instance_service.get.return_value = Mock(consumer_key="XXX")
        pyramid_request.params["query"] = "some-value"
        response = AdminViews(pyramid_request).find_instance()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", consumer_key="XXX")
        )

    def test_show_instance(self, pyramid_request, application_instance_service):
        application_instance_service.get.return_value = sentinel.instance
        pyramid_request.matchdict["consumer_key"] = "XXX"
        response = AdminViews(pyramid_request).show_instance()

        assert response == {"instance": sentinel.instance}

    def test_show_not_found(self, pyramid_request, application_instance_service):
        application_instance_service.get.return_value = None
        pyramid_request.matchdict["consumer_key"] = "XXX"

        with pytest.raises(HTTPNotFound):
            AdminViews(pyramid_request).show_instance()

    def test_update_instance(self, pyramid_request, application_instance_service):
        application_instance_service.get.return_value = Mock(consumer_key="XXX")
        pyramid_request.matchdict["consumer_key"] = "XXX"
        response = AdminViews(pyramid_request).update_instance()

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", consumer_key="XXX")
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminViews(pyramid_request)
