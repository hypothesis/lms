from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound

from lms.services import ApplicationInstanceNotFound
from lms.views.admin import AdminViews, logged_out, notfound
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("pyramid_config", "application_instance_service")
class TestAdminViews:
    def test_index(self, pyramid_request, views):
        response = views.index()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_instances(self, views):
        response = views.instances()

        assert response == {}

    def test_find_instance_no_query(self, views):

        with pytest.raises(HTTPBadRequest):
            views.find_instance()

    def test_find_instance_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.params["query"] = "some-value"
        response = AdminViews(pyramid_request).find_instance()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_find_instance_found(self, pyramid_request, application_instance_service):
        pyramid_request.params["query"] = sentinel.consumer_key

        response = AdminViews(pyramid_request).find_instance()

        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance",
                consumer_key=application_instance_service.get_by_consumer_key.return_value.consumer_key,
            )
        )

    def test_show_instance(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        response = AdminViews(pyramid_request).show_instance()
        assert (
            response["instance"].consumer_key
            == application_instance_service.get_by_consumer_key.return_value.consumer_key
        )

    def test_show_not_found(self, pyramid_request, application_instance_service):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminViews(pyramid_request).show_instance()

    def test_update_instance(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        response = AdminViews(pyramid_request).update_instance()

        application_instance_service.get_by_consumer_key.assert_called_once_with(
            sentinel.consumer_key
        )
        application_instance = (
            application_instance_service.get_by_consumer_key.return_value
        )

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance", consumer_key=application_instance.consumer_key
            )
        )

    @pytest.mark.parametrize(
        "setting,sub_setting",
        (
            ("canvas", "groups_enabled"),
            ("canvas", "sections_enabled"),
            ("blackboard", "files_enabled"),
            ("blackboard", "groups_enabled"),
            ("microsoft_onedrive", "files_enabled"),
            ("vitalsource", "enabled"),
            ("jstor", "enabled"),
        ),
    )
    @pytest.mark.parametrize("enabled", (True, False))
    def test_update_instance_saves_ai_settings(
        self,
        pyramid_request,
        application_instance_service,
        setting,
        sub_setting,
        enabled,
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        if enabled:
            pyramid_request.params[f"{setting}.{sub_setting}"] = "on"

        AdminViews(pyramid_request).update_instance()

        application_instance = (
            application_instance_service.get_by_consumer_key.return_value
        )
        assert application_instance.settings.get(setting, sub_setting) == enabled

    def test_update_instance_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminViews(pyramid_request).update_instance()

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminViews(pyramid_request)


def test_logged_out_redirects_to_login(pyramid_request):
    response = logged_out(pyramid_request)

    assert response.status_code == 302

    assert response == temporary_redirect_to(
        pyramid_request.route_url("pyramid_googleauth.login")
    )


def test_not_found_view(pyramid_request):
    response = notfound(pyramid_request)

    assert response.status_code == 404
