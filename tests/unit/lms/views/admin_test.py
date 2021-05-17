from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPBadRequest, HTTPNotFound

from lms.services import ConsumerKeyError
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
        application_instance_service.get.side_effect = ConsumerKeyError
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
                consumer_key=application_instance_service.get.return_value.consumer_key,
            )
        )

    def test_show_instance(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        response = AdminViews(pyramid_request).show_instance()
        assert (
            response["instance"].consumer_key
            == application_instance_service.get.return_value.consumer_key
        )

    def test_show_not_found(self, pyramid_request, application_instance_service):
        application_instance_service.get.side_effect = ConsumerKeyError
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminViews(pyramid_request).show_instance()

    @pytest.mark.parametrize(
        "sections_enabled,groups_enabled",
        [
            (False, False),
            (True, False),
            (True, True),
            (True, True),
        ],
    )
    def test_update_instance(
        self,
        pyramid_request,
        application_instance_service,
        sections_enabled,
        groups_enabled,
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        if sections_enabled:
            # If the user checks the "Sections enabled" box then request.params
            # contains the string "on" for "sections_enabled".
            pyramid_request.params["sections_enabled"] = "on"
        else:
            # If the "Sections enabled" box is un-checked then
            # "sections_enabled" is missing from request.params.
            pass

        if groups_enabled:
            # If the user checks the "Groups enabled" box then request.params
            # contains the string "on" for "groups_enabled".
            pyramid_request.params["groups_enabled"] = "on"
        else:
            # If the "Groups enabled" box is un-checked then
            # "groups_enabled" is missing from request.params.
            pass

        response = AdminViews(pyramid_request).update_instance()

        application_instance_service.get.assert_called_once_with(sentinel.consumer_key)
        application_instance = application_instance_service.get.return_value
        assert (
            application_instance.settings.get("canvas", "groups_enabled")
            == groups_enabled
        )
        assert (
            application_instance.settings.get("canvas", "sections_enabled")
            == sections_enabled
        )
        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance",
                consumer_key=application_instance_service.get.return_value.consumer_key,
            )
        )

    def test_update_instance_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get.side_effect = ConsumerKeyError
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
