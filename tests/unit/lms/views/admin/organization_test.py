from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound

from lms.views.admin.organization import AdminOrganizationViews
from tests import factories


class TestAdminOrganizationViews:
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

    @pytest.mark.parametrize("value,expected", [("", None), (" name", "name")])
    def test_update_organization_name(
        self, pyramid_request, organization_service, views, value, expected
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        pyramid_request.params["name"] = value
        organization_service.get_by_id.return_value = factories.Organization()

        response = views.update_organization()
        org = response["org"]

        assert org == organization_service.get_by_id.return_value
        assert org.name == expected

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminOrganizationViews(pyramid_request)
