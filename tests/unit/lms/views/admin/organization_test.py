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

    @pytest.mark.parametrize("name", ["  ", " name"])
    def test_update_organization_name(
        self, pyramid_request, organization_service, views, name
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        pyramid_request.params["name"] = name
        organization_service.get_by_id.return_value = factories.Organization()

        response = views.update_organization()

        organization_service.update_organization.assert_called_once_with(
            organization_service.get_by_id.return_value,
            name=name.strip() if name else "",
        )
        org = response["org"]
        assert org == organization_service.get_by_id.return_value

    @pytest.mark.parametrize("value,expected", [("", False), ("on", True)])
    def test_toggle_organization_enabled(
        self,
        value,
        expected,
        pyramid_request,
        organization_service,
        views,
        AuditTrailEvent,
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        pyramid_request.params["enabled"] = value
        organization_service.get_by_id.return_value = factories.Organization()

        views.toggle_organization_enabled()

        organization_service.update_organization(
            organization_service.get_by_id.return_value, enabled=expected
        )
        AuditTrailEvent.notify.assert_called_once_with(
            pyramid_request, organization_service.get_by_id.return_value
        )

    @pytest.fixture
    def AuditTrailEvent(self, patch):
        return patch("lms.views.admin.organization.AuditTrailEvent")

    def test_search_by_public_id(self, pyramid_request, organization_service, views):
        pyramid_request.params["public_id"] = sentinel.public_id

        result = views.search()

        organization_service.get_by_public_id.assert_called_once_with(
            sentinel.public_id
        )
        assert result == {
            "organizations": [organization_service.get_by_public_id.return_value]
        }

    def test_search_by_name(self, pyramid_request, organization_service, views):
        pyramid_request.params["name"] = "   NAME "

        result = views.search()

        organization_service.search.assert_called_once_with(name="NAME")
        assert result == {"organizations": organization_service.search.return_value}

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminOrganizationViews(pyramid_request)
