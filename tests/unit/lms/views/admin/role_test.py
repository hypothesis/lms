from unittest.mock import sentinel

import pytest

from lms.views.admin.role import AdminRoleViews
from tests import factories
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("application_instance_service")
class TestAdminRoleViews:
    def test_new_override(
        self, pyramid_request, application_instance_service, lti_role_service, views
    ):
        lti_role_service.search.return_value = factories.LTIRole.create_batch(5)
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.new_override()

        application_instance_service.get_by_id.assert_called_once_with(id_=sentinel.id)
        lti_role_service.search.assert_called_once()
        assert response == {
            "instance": application_instance_service.get_by_id.return_value,
            "existing_roles": [
                (role.id, role.value) for role in lti_role_service.search.return_value
            ],
        }

    def test_new_override_post(
        self,
        pyramid_request,
        application_instance_service,
        lti_role_service,
        views,
        AuditTrailEvent,
    ):
        pyramid_request.matchdict["id_"] = sentinel.id
        pyramid_request.params["role_id"] = sentinel.role_id
        pyramid_request.params["type"] = sentinel.type
        pyramid_request.params["scope"] = sentinel.scope

        response = views.new_override_post()

        application_instance_service.get_by_id.assert_called_once_with(id_=sentinel.id)
        lti_role_service.search.assert_called_once_with(id_=sentinel.role_id)
        lti_role_service.new_role_override.assert_called_once_with(
            application_instance_service.get_by_id.return_value,
            lti_role_service.search.return_value.one.return_value,
            sentinel.type,
            sentinel.scope,
        )
        AuditTrailEvent.notify.assert_called_once_with(
            pyramid_request, lti_role_service.new_role_override.return_value
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.section",
                id_=application_instance_service.get_by_id.return_value.id,
                section="role-overrides",
            )
        )

    def test_show(self, pyramid_request, lti_role_service, views):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.show()

        lti_role_service.search_override.assert_called_once_with(id_=sentinel.id)
        assert response == {
            "override": lti_role_service.search_override.return_value.one.return_value,
            "existing_roles": [
                (role.id, role.value) for role in lti_role_service.search.return_value
            ],
        }

    def test_update(self, pyramid_request, lti_role_service, views, AuditTrailEvent):
        pyramid_request.matchdict["id_"] = sentinel.id
        pyramid_request.params["type"] = sentinel.type
        pyramid_request.params["scope"] = sentinel.scope

        response = views.update()

        lti_role_service.search_override.assert_called_once_with(id_=sentinel.id)
        override = lti_role_service.search_override.return_value.one.return_value
        lti_role_service.update_override.assert_called_once_with(
            override, scope=sentinel.scope, type_=sentinel.type
        )
        AuditTrailEvent.notify.assert_called_once_with(pyramid_request, override)
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.role.override", id_=override.id)
        )

    def test_delete(self, pyramid_request, lti_role_service, views, AuditTrailEvent):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = views.delete()

        lti_role_service.search_override.assert_called_once_with(id_=sentinel.id)
        override = lti_role_service.search_override.return_value.one.return_value
        lti_role_service.delete_override.assert_called_once_with(override)
        AuditTrailEvent.notify.assert_called_once_with(pyramid_request, override)
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.section",
                id_=override.application_instance_id,
                section="role-overrides",
            )
        )

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminRoleViews(pyramid_request)

    @pytest.fixture
    def AuditTrailEvent(self, patch):
        return patch("lms.views.admin.role.AuditTrailEvent")
