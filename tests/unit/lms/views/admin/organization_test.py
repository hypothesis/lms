from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.views.admin.organization import AdminOrganizationViews
from tests import factories


class TestAdminOrganizationViews:
    def test_show_organization(self, pyramid_request, organization_service, views):
        pyramid_request.matchdict["public_id"] = sentinel.public_id

        response = views.show_organization()

        organization_service.get_by_public_id.assert_called_once_with(
            sentinel.public_id
        )
        assert response["org"] == organization_service.get_by_public_id.return_value

    def test_show_organization_not_found(
        self, pyramid_request, organization_service, views
    ):
        pyramid_request.matchdict["public_id"] = sentinel.public_id
        organization_service.get_by_public_id.return_value = None

        with pytest.raises(HTTPNotFound):
            views.show_organization()

        organization_service.get_by_public_id.assert_called_once_with(
            sentinel.public_id
        )

    @pytest.mark.parametrize("value,expected", [("", None), (" name", "name")])
    def test_update_organization_name(
        self, pyramid_request, organization_service, views, value, expected
    ):
        pyramid_request.matchdict["public_id"] = sentinel.public_id
        pyramid_request.params["name"] = value
        organization_service.get_by_public_id.return_value = factories.Organization()

        response = views.update_organization()
        org = response["org"]

        assert org == organization_service.get_by_public_id.return_value
        assert org.name == expected

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminOrganizationViews(pyramid_request)
