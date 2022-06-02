from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.exc import IntegrityError

from lms.services import ApplicationInstanceNotFound
from lms.views.admin.application_instance import AdminApplicationInstanceViews
from tests.matchers import Any, temporary_redirect_to


@pytest.mark.usefixtures(
    "pyramid_config", "application_instance_service", "lti_registration_service"
)
class TestAdminApplicationInstanceViews:
    def test_instances(self, views):
        assert views.instances() == {}

    def test_instance_new(
        self, pyramid_request_new_instance, application_instance_service
    ):
        response = AdminApplicationInstanceViews(
            pyramid_request_new_instance
        ).instance_new()

        application_instance_service.create.assert_called_once_with(
            lms_url="LMS_URL",
            email="EMAIL",
            deployment_id="DEPLOYMENT_ID",
            developer_key="",
            developer_secret="",
            lti_registration_id=sentinel.lti_registration_id,
        )

        assert response == temporary_redirect_to(
            pyramid_request_new_instance.route_url(
                "admin.instance.id",
                id_=application_instance_service.create.return_value.id,
            )
        )

    @pytest.mark.parametrize("missing", ["lms_url", "email", "deployment_id"])
    def test_instance_new_missing_params(self, pyramid_request_new_instance, missing):
        del pyramid_request_new_instance.params[missing]

        response = AdminApplicationInstanceViews(
            pyramid_request_new_instance
        ).instance_new()

        assert response.status_code == 400

    def test_instance_with_duplicate(
        self, pyramid_request_new_instance, application_instance_service
    ):
        application_instance_service.create.side_effect = IntegrityError(
            Any(), Any(), Any()
        )

        response = AdminApplicationInstanceViews(
            pyramid_request_new_instance
        ).instance_new()

        assert response.status_code == 400

    def test_search_not_query(self, pyramid_request):
        response = AdminApplicationInstanceViews(pyramid_request).search()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_search_no_results(self, pyramid_request, application_instance_service):
        application_instance_service.search.return_value = None
        pyramid_request.params["issuer"] = sentinel.issuer

        response = AdminApplicationInstanceViews(pyramid_request).search()

        application_instance_service.search.assert_called_once_with(
            consumer_key=None,
            issuer=sentinel.issuer,
            client_id=None,
            deployment_id=None,
            tool_consumer_instance_guid=None,
        )
        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_search_single_result(
        self, pyramid_request, application_instance_service, application_instance
    ):
        application_instance_service.search.return_value = [application_instance]
        pyramid_request.params["issuer"] = sentinel.issuer

        response = AdminApplicationInstanceViews(pyramid_request).search()

        application_instance_service.search.assert_called_once_with(
            consumer_key=None,
            issuer=sentinel.issuer,
            client_id=None,
            deployment_id=None,
            tool_consumer_instance_guid=None,
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id",
                id_=application_instance_service.search.return_value[0].id,
            )
        )

    def test_search_multiple_results(
        self, pyramid_request, application_instance_service
    ):
        pyramid_request.params = {
            "consumer_key": sentinel.consumer_key,
            "issuer": sentinel.issuer,
            "client_id": sentinel.client_id,
            "deployment_id": sentinel.deployment_id,
            "tool_consumer_instance_guid": sentinel.tool_consumer_instance_guid,
        }

        response = AdminApplicationInstanceViews(pyramid_request).search()

        application_instance_service.search.assert_called_once_with(
            consumer_key=sentinel.consumer_key,
            issuer=sentinel.issuer,
            client_id=sentinel.client_id,
            deployment_id=sentinel.deployment_id,
            tool_consumer_instance_guid=sentinel.tool_consumer_instance_guid,
        )
        assert response == {
            "instances": application_instance_service.search.return_value
        }

    def test_show_instance_consumer_key(
        self, pyramid_request, application_instance_service
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        response = AdminApplicationInstanceViews(pyramid_request).show_instance()

        assert (
            response["instance"].consumer_key
            == application_instance_service.get_by_consumer_key.return_value.consumer_key
        )

    def test_show_instance_id(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["id_"] = sentinel.id

        response = AdminApplicationInstanceViews(pyramid_request).show_instance()

        assert (
            response["instance"].id
            == application_instance_service.get_by_id.return_value.id
        )

    def test_show_not_found(self, pyramid_request, application_instance_service):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminApplicationInstanceViews(pyramid_request).show_instance()

    def test_update_instance(self, pyramid_request, application_instance_service):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        response = AdminApplicationInstanceViews(pyramid_request).update_instance()

        application_instance_service.get_by_consumer_key.assert_called_once_with(
            sentinel.consumer_key
        )
        application_instance = (
            application_instance_service.get_by_consumer_key.return_value
        )

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance.id", id_=application_instance.id)
        )

    @pytest.mark.parametrize(
        "setting,sub_setting,value,expected",
        (
            # Boolean fields
            ("canvas", "groups_enabled", "on", True),
            ("canvas", "sections_enabled", "", False),
            ("blackboard", "files_enabled", "other", False),
            ("blackboard", "groups_enabled", "off", False),
            ("microsoft_onedrive", "files_enabled", "on", True),
            ("vitalsource", "enabled", "on", True),
            ("jstor", "enabled", "off", False),
            # String fields
            ("jstor", "site_code", "CODE", "CODE"),
            ("jstor", "site_code", "  CODE  ", "CODE"),
            ("jstor", "site_code", "", None),
            ("jstor", "site_code", None, None),
        ),
    )
    def test_update_instance_saves_ai_settings(
        self,
        pyramid_request,
        application_instance_service,
        setting,
        sub_setting,
        value,
        expected,
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        pyramid_request.params[f"{setting}.{sub_setting}"] = value

        AdminApplicationInstanceViews(pyramid_request).update_instance()

        application_instance = (
            application_instance_service.get_by_consumer_key.return_value
        )
        assert application_instance.settings.get(setting, sub_setting) == expected

    def test_update_instance_not_found(
        self, pyramid_request, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            AdminApplicationInstanceViews(pyramid_request).update_instance()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params = {}
        return pyramid_request

    @pytest.fixture
    def pyramid_request_new_instance(self, pyramid_request):
        pyramid_request.params["lms_url"] = "LMS_URL"
        pyramid_request.params["email"] = "EMAIL"
        pyramid_request.params["deployment_id"] = "DEPLOYMENT_ID"

        pyramid_request.matchdict["id_"] = sentinel.lti_registration_id

        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminApplicationInstanceViews(pyramid_request)
