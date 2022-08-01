from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.exc import IntegrityError

from lms.services import ApplicationInstanceNotFound
from lms.views.admin.application_instance import AdminApplicationInstanceViews
from tests import factories
from tests.matchers import Any, temporary_redirect_to


@pytest.mark.usefixtures(
    "pyramid_config", "application_instance_service", "lti_registration_service"
)
class TestAdminApplicationInstanceViews:
    def test_instances(self, views):
        assert views.instances() == {}

    @pytest.mark.usefixtures("with_form_submission")
    def test_new_instance(self, application_instance_service, views, pyramid_request):
        response = views.new_instance()

        application_instance_service.create_application_instance.assert_called_once_with(
            lms_url="http://lms-url.com",
            email="test@email.com",
            deployment_id="DEPLOYMENT_ID",
            developer_key="",
            developer_secret="",
            lti_registration_id=sentinel.lti_registration_id,
        )

        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id",
                id_=application_instance_service.create_application_instance.return_value.id,
            )
        )

    @pytest.mark.usefixtures("with_form_submission")
    @pytest.mark.parametrize("missing", ["lms_url", "email", "deployment_id"])
    def test_instance_new_missing_params(self, views, missing, pyramid_request):
        del pyramid_request.POST[missing]

        response = views.new_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_form_submission")
    def test_instance_with_duplicate(self, views, application_instance_service):
        application_instance_service.create_application_instance.side_effect = (
            IntegrityError(Any(), Any(), Any())
        )

        response = views.new_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance(
        self,
        application_instance_service,
        views,
        pyramid_request,
        application_instance,
        lti_registration_service,
    ):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        assert not application_instance.lti_registration

        response = views.new_instance()

        application_instance_service.get_by_consumer_key(
            application_instance.consumer_key
        )

        assert application_instance.lti_registration == lti_registration
        assert (
            application_instance.deployment_id
            == pyramid_request.params["deployment_id"]
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance.id", id_=application_instance.id)
        )

    @pytest.mark.usefixtures("with_upgrade_form")
    @pytest.mark.parametrize("parameter", ["lms_url", "email"])
    def test_upgrade_instance_allows_empty(
        self,
        views,
        pyramid_request,
        parameter,
        lti_registration_service,
        application_instance,
    ):
        lti_registration_service.get_by_id.return_value = factories.LTIRegistration()

        # Replicate real's pyramid_request behavkour
        pyramid_request.POST[parameter] = ""
        pyramid_request.params[parameter] = ""

        response = views.new_instance()

        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance.id", id_=application_instance.id)
        )

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_no_deployment_id(self, views, pyramid_request):
        del pyramid_request.POST["deployment_id"]

        response = views.new_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_already_upgraded(self, views, application_instance):
        application_instance.lti_registration_id = 100
        application_instance.deployment_id = "ID"

        response = views.new_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_duplicate(self, views, lti_registration_service):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        factories.ApplicationInstance(
            lti_registration=lti_registration, deployment_id="DEPLOYMENT_ID"
        )

        response = views.new_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_non_existing_instance(self, views, application_instance_service):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        response = views.new_instance()

        assert response.status_code == 400

    def test_search_not_query(self, pyramid_request, views):
        response = views.search()

        assert pyramid_request.session.peek_flash("errors")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instances")
        )

    def test_search_no_results(
        self, pyramid_request, application_instance_service, views
    ):
        application_instance_service.search.return_value = None
        pyramid_request.params["issuer"] = sentinel.issuer

        response = views.search()

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
        self, pyramid_request, application_instance_service, application_instance, views
    ):
        application_instance_service.search.return_value = [application_instance]
        pyramid_request.params["issuer"] = sentinel.issuer

        response = views.search()

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
        self, pyramid_request, application_instance_service, views
    ):
        pyramid_request.params = {
            "consumer_key": sentinel.consumer_key,
            "issuer": sentinel.issuer,
            "client_id": sentinel.client_id,
            "deployment_id": sentinel.deployment_id,
            "tool_consumer_instance_guid": sentinel.tool_consumer_instance_guid,
        }

        response = views.search()

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

    def test_show_not_found(self, pyramid_request, application_instance_service, views):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        with pytest.raises(HTTPNotFound):
            views.show_instance()

    def test_update_instance(
        self, pyramid_request, application_instance_service, views
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key

        response = views.update_instance()

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
        "setting,value,expected",
        (
            ("lms_url", "http://some-url.com", "http://some-url.com"),
            ("custom_canvas_api_domain", "some.domain.com", "some.domain.com"),
            ("deployment_id", "DEPLOYMENT_ID", "DEPLOYMENT_ID"),
        ),
    )
    def test_update_instance_save_ai_fields(
        self, setting, value, expected, pyramid_request, application_instance
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        pyramid_request.params[setting] = value

        AdminApplicationInstanceViews(pyramid_request).update_instance()

        assert getattr(application_instance, setting) == expected

    @pytest.mark.parametrize(
        "setting,value",
        (
            ("lms_url", ""),
            ("custom_canvas_api_domain", ""),
            ("deployment_id", "    "),
        ),
    )
    def test_update_instance_save_ai_fields_keeps_existing(
        self, setting, value, pyramid_request, application_instance
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        pyramid_request.params[setting] = value

        existing_value = getattr(application_instance, setting)

        AdminApplicationInstanceViews(pyramid_request).update_instance()

        assert getattr(application_instance, setting) == existing_value

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
            ("vitalsource", "user_lti_param", "user_id", "user_id"),
            ("vitalsource", "api_key", "api_key", "api_key"),
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
    def with_form_submission(self, pyramid_request):
        application_instance_data = {
            "lms_url": "http://lms-url.com",
            "email": "test@email.com",
            "deployment_id": "DEPLOYMENT_ID",
        }
        pyramid_request.matchdict["id_"] = sentinel.lti_registration_id
        # Real pyramid request have the same params available
        # via POST and params
        pyramid_request.POST.update(application_instance_data)
        pyramid_request.params.update(application_instance_data)

        return pyramid_request

    @pytest.fixture
    def with_upgrade_form(self, with_form_submission, application_instance):
        with_form_submission.params["consumer_key"] = application_instance.consumer_key
        return with_form_submission

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminApplicationInstanceViews(pyramid_request)
