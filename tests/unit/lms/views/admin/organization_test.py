from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.views.admin.organization import AdminOrganizationViews
from tests import factories
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("organization_service")
class TestAdminOrganizationViews:
    def test_new_organization_callback(
        self, pyramid_request, organization_service, views
    ):
        pyramid_request.POST["name"] = "NAME"

        response = views.new_organization_callback()

        organization_service.create_organization.assert_called_once_with(name="NAME")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.organization",
                id_=organization_service.create_organization.return_value.id,
            )
        )

    def test_new_organization_callback_invalid_payload(self, views):
        assert not views.new_organization_callback()

    def test_show_organization(self, pyramid_request, organization_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id_

        response = views.show_organization()

        organization_service.get_by_id.assert_called_once_with(sentinel.id_)
        assert response["org"] == organization_service.get_by_id.return_value

    def test_show_organization_not_found(
        self, pyramid_request, organization_service, views
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        organization_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show_organization()

        organization_service.get_by_id.assert_called_once_with(sentinel.id_)

    @pytest.mark.parametrize("name,expected_name", [("", ""), (" name", "name")])
    @pytest.mark.parametrize("enabled, expected_enabled", [("on", True), ("", False)])
    def test_update_organization(
        self,
        pyramid_request,
        organization_service,
        views,
        name,
        expected_name,
        enabled,
        expected_enabled,
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        pyramid_request.params = {"name": name, "enabled": enabled}
        organization_service.get_by_id.return_value = factories.Organization()

        response = views.update_organization()
        org = response["org"]

        organization_service.update_organization.assert_called_once_with(
            org, name=expected_name, enabled=expected_enabled
        )
        assert org == organization_service.get_by_id.return_value

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminOrganizationViews(pyramid_request)
