from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance
from lms.services import ApplicationInstanceNotFound
from lms.validation import ValidationError
from lms.views.admin.application_instance import AdminApplicationInstanceViews
from tests import factories
from tests.matchers import Any, temporary_redirect_to


@pytest.mark.usefixtures(
    "pyramid_config",
    "application_instance_service",
    "lti_registration_service",
    "organization_service",
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

    def test_downgrade_instance(
        self,
        views,
        pyramid_request,
        application_instance_lti_13,
        application_instance_service,
    ):
        application_instance_service.get_by_id.return_value = (
            application_instance_lti_13
        )

        response = views.downgrade_instance()

        assert not application_instance_lti_13.lti_registration_id
        assert not application_instance_lti_13.deployment_id
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id", id_=application_instance_lti_13.id
            )
        )

    def test_downgrade_instance_no_lti13(
        self,
        views,
        pyramid_request,
        application_instance,
        application_instance_service,
    ):
        application_instance_service.get_by_id.return_value = application_instance

        views.downgrade_instance()

        assert pyramid_request.session.peek_flash("errors")

    def test_downgrade_instance_no_consumer_key(
        self,
        views,
        pyramid_request,
        application_instance_service,
        application_instance_lti_13,
    ):
        application_instance_lti_13.consumer_key = None
        application_instance_service.get_by_id.return_value = (
            application_instance_lti_13
        )

        application_instance_service.get_by_id.return_value = (
            application_instance_lti_13
        )

        views.downgrade_instance()

        assert pyramid_request.session.peek_flash("errors")

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

        response = views.upgrade_instance()

        application_instance_service.get_by_consumer_key.assert_called_once_with(
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
    def test_upgrade_no_deployment_id(self, views, pyramid_request):
        del pyramid_request.POST["deployment_id"]

        response = views.upgrade_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_already_upgraded(self, views, application_instance):
        application_instance.lti_registration_id = 100
        application_instance.deployment_id = "ID"

        response = views.upgrade_instance()

        assert response.status_code == 400

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_duplicate(self, views, db_session, lti_registration_service):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        factories.ApplicationInstance(
            lti_registration=lti_registration, deployment_id="DEPLOYMENT_ID"
        )

        response = views.upgrade_instance()

        assert response.status_code == 400

        # Show that the DB connection has not been permanently broken. This
        # would cause us to fail completely when trying to present the error.
        # We are checking we do _not_ raise `PendingRollbackError` here.
        db_session.query(ApplicationInstance).all()

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_non_existing_instance(self, views, application_instance_service):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        response = views.upgrade_instance()

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

    @pytest.mark.parametrize("key,", (" ", " key "))
    @pytest.mark.parametrize("secret", (" ", " secret "))
    @pytest.mark.parametrize("lms_url", (" ", "http://some-url.com    "))
    @pytest.mark.parametrize("deployment_id", (" ", " DEPLOYMENT_ID"))
    def test_update_application_instance(
        self,
        pyramid_request,
        application_instance_service,
        views,
        key,
        secret,
        lms_url,
        deployment_id,
    ):
        pyramid_request.params = {
            "developer_key": key,
            "developer_secret": secret,
            "lms_url": lms_url,
            "deployment_id": deployment_id,
            "org_public_id": "",
        }

        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            application_instance_service.get_by_id.return_value,
            lms_url=lms_url.strip() if lms_url else "",
            deployment_id=deployment_id.strip() if deployment_id else "",
            developer_key=key.strip() if key else "",
            developer_secret=secret.strip() if secret else "",
            organization_id=application_instance_service.get_by_id.return_value.organization_id,
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
            ("vitalsource", "api_key", "api_key", "api_key"),
            ("vitalsource", "user_lti_param", "user_id", "user_id"),
            ("vitalsource", "user_lti_pattern", "name_(.*)", "name_(.*)"),
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

    def test_update_application_instance_organization_id(
        self, pyramid_request, application_instance_service, views
    ):

        pyramid_request.params["org_public_id"] = "PUBLIC_ID"

        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            application_instance_service.get_by_id.return_value,
            lms_url=Any(),
            deployment_id=Any(),
            developer_key=Any(),
            developer_secret=Any(),
            organization_public_id="PUBLIC_ID",
        )

    def test_update_application_instance_not_found_organization_id(
        self, pyramid_request, application_instance_service, views, organization_service
    ):

        pyramid_request.params["org_public_id"] = "PUBLIC_ID"
        organization_service.get_by_public_id.return_value = None

        response = views.update_instance()

        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id",
                id_=application_instance_service.get_by_id.return_value.id,
            )
        )

    def test_update_application_instance_invalid_organization_id(
        self, pyramid_request, application_instance_service, views, organization_service
    ):

        pyramid_request.params["org_public_id"] = "PUBLIC_ID"
        organization_service.get_by_public_id.side_effect = ValidationError(
            messages=sentinel.messages
        )

        response = views.update_instance()

        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id",
                id_=application_instance_service.get_by_id.return_value.id,
            )
        )

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
    def application_instance_lti_13(self, application_instance, db_session):
        lti_registration = factories.LTIRegistration()
        # Get an valid ID for the registration
        db_session.flush()
        application_instance.lti_registration_id = lti_registration.id
        application_instance.deployment_id = "ID"

        return application_instance

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
        with_form_submission.params["consumer_key"] = with_form_submission.POST[
            "consumer_key"
        ] = application_instance.consumer_key
        return with_form_submission

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminApplicationInstanceViews(pyramid_request)
