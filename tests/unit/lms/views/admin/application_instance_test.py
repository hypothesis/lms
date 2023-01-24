from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance
from lms.models.public_id import InvalidPublicId
from lms.services import ApplicationInstanceNotFound
from lms.validation import ValidationError
from lms.views.admin.application_instance import AdminApplicationInstanceViews
from tests import factories
from tests.matchers import Any, temporary_redirect_to

REDIRECT_TO_NEW_AI = Any.instance_of(HTTPFound).with_attrs(
    {"location": Any.string.containing("/admin/instance/new")}
)


@pytest.mark.usefixtures(
    "pyramid_config",
    "application_instance_service",
    "lti_registration_service",
    "organization_service",
    "aes_service",
)
class TestAdminApplicationInstanceViews:
    def test_instances(self, views):
        assert views.instances() == {}

    @pytest.mark.parametrize("lti_registration_id", ("123", "  123   "))
    def test_new_instance_start_v13(
        self, views, pyramid_request, lti_registration_service, lti_registration_id
    ):
        pyramid_request.params = {
            "lti_registration_id": lti_registration_id,
            "key_1": "value_1",
            "key_2": "value_2",
        }

        response = views.new_instance_start()

        lti_registration_service.get_by_id.assert_called_once_with("123")
        assert response == dict(
            pyramid_request.params,
            lti_registration=lti_registration_service.get_by_id.return_value,
        )

    def test_new_instance_start_v11(self, views, pyramid_request):
        pyramid_request.params["lti_registration_id"] = None

        response = views.new_instance_start()

        assert not response["lti_registration"]

    @pytest.mark.usefixtures("ai_new_params_v13")
    def test_new_instance_callback_v13(self, views, application_instance_service):
        application_instance_service.create_application_instance.return_value.id = 12345

        response = views.new_instance_callback()

        application_instance_service.create_application_instance.assert_called_once_with(
            lms_url="http://example.com",
            email="test@example.com",
            deployment_id="22222",
            developer_key="DEVELOPER_KEY",
            developer_secret="DEVELOPER_SECRET",
            organization_public_id="us.lms.org.ID",
            lti_registration_id=54321,
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": Any.string.containing("/admin/instance/id/12345")}
        )

    @pytest.mark.usefixtures("ai_new_params_v11")
    def test_new_instance_callback_v11(self, views):
        response = views.new_instance_callback()

        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": Any.string.containing("/admin/instance/id/")}
        )

    @pytest.mark.usefixtures("ai_new_params_v13")
    @pytest.mark.parametrize(
        "exception", (IntegrityError(Any(), Any(), Any()), InvalidPublicId)
    )
    def test_new_instance_callback_with_errors(
        self, views, application_instance_service, exception
    ):
        application_instance_service.create_application_instance.side_effect = exception

        response = views.new_instance_callback()

        assert response == REDIRECT_TO_NEW_AI

    _V11_NEW_AI_BAD_FIELDS = [
        ("lms_url", "not a url"),
        ("email", "not an email"),
        ("organization_public_id", None),
    ]

    @pytest.mark.parametrize(
        "param,bad_value", _V11_NEW_AI_BAD_FIELDS + [("deployment_id", None)]
    )
    def test_new_instance_callback_v13_required_fields(
        self, views, ai_new_params_v13, param, bad_value
    ):
        ai_new_params_v13[param] = bad_value

        response = views.new_instance_callback()

        assert response == REDIRECT_TO_NEW_AI

    @pytest.mark.parametrize("param,bad_value", _V11_NEW_AI_BAD_FIELDS)
    def test_new_instance_callback_v11_required_fields(
        self, views, ai_new_params_v11, param, bad_value
    ):
        ai_new_params_v11[param] = bad_value

        response = views.new_instance_callback()

        assert response == REDIRECT_TO_NEW_AI

    def test_move_application_instance_org(
        self, views, pyramid_request, application_instance, application_instance_service
    ):
        application_instance_service.get_by_id.return_value = application_instance
        pyramid_request.params["org_public_id"] = "PUBLIC_ID"

        response = views.move_application_instance_org()

        application_instance_service.update_application_instance.assert_called_once_with(
            application_instance, organization_public_id="PUBLIC_ID"
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance.id", id_=application_instance.id)
        )

    def test_move_application_instance_org_invalid_organization_id(
        self, pyramid_request, application_instance_service, views
    ):
        pyramid_request.params["org_public_id"] = "PUBLIC_ID"
        application_instance_service.update_application_instance.side_effect = (
            ValidationError(messages=sentinel.messages)
        )

        response = views.move_application_instance_org()

        assert pyramid_request.session.peek_flash("validation")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance.id",
                id_=application_instance_service.get_by_id.return_value.id,
            )
        )

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
        self, views, pyramid_request, application_instance, application_instance_service
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

        assert views.upgrade_instance() == REDIRECT_TO_NEW_AI

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_already_upgraded(self, views, application_instance):
        application_instance.lti_registration_id = 100
        application_instance.deployment_id = "ID"

        assert views.upgrade_instance() == REDIRECT_TO_NEW_AI

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_duplicate(self, views, db_session, lti_registration_service):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        factories.ApplicationInstance(
            lti_registration=lti_registration, deployment_id="DEPLOYMENT_ID"
        )

        response = views.upgrade_instance()

        assert response == REDIRECT_TO_NEW_AI

        # Show that the DB connection has not been permanently broken. This
        # would cause us to fail completely when trying to present the error.
        # We are checking we do _not_ raise `PendingRollbackError` here.
        db_session.query(ApplicationInstance).all()

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_non_existing_instance(self, views, application_instance_service):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        assert views.upgrade_instance() == REDIRECT_TO_NEW_AI

    def test_search(self, pyramid_request, application_instance_service, views):
        pyramid_request.params = pyramid_request.POST = dict(
            id="1",
            consumer_key="CONSUMER_KEY",
            issuer="ISSUER",
            client_id="CLIENT_ID",
            deployment_id="DEPLOYMENT_ID",
            tool_consumer_instance_guid="TOOL_CONSUMER_INSTANCE_GUID",
        )

        response = views.search()

        application_instance_service.search.assert_called_once_with(
            id_="1",
            consumer_key="CONSUMER_KEY",
            issuer="ISSUER",
            client_id="CLIENT_ID",
            deployment_id="DEPLOYMENT_ID",
            tool_consumer_instance_guid="TOOL_CONSUMER_INSTANCE_GUID",
        )
        assert response == {
            "instances": application_instance_service.search.return_value
        }

    def test_search_invalid(self, pyramid_request, views):
        pyramid_request.POST = {"id": "not a number"}

        assert not views.search()
        assert pyramid_request.session.peek_flash

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

    def test_update_application_instance(
        self, pyramid_request, application_instance_service, views
    ):
        pyramid_request.params = {
            "lms_url": "   http://example.com    ",
            "deployment_id": " DEPLOYMENT_ID  ",
            "developer_key": "  DEVELOPER KEY  ",
            "developer_secret": " DEVELOPER SECRET  ",
        }

        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            application_instance_service.get_by_id.return_value,
            lms_url="http://example.com",
            deployment_id="DEPLOYMENT_ID",
            developer_key="DEVELOPER KEY",
            developer_secret="DEVELOPER SECRET",
        )

    def test_update_application_instance_with_no_arguments(
        self, views, application_instance_service
    ):
        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            application_instance_service.get_by_id.return_value,
            lms_url="",
            deployment_id="",
            developer_key="",
            developer_secret="",
        )

    @pytest.mark.parametrize(
        "setting,sub_setting,value,expected",
        (
            # Boolean fields
            ("canvas", "groups_enabled", "on", True),
            ("canvas", "sections_enabled", "", False),
            ("blackboard", "files_enabled", "other", False),
            ("blackboard", "groups_enabled", "off", False),
            ("desire2learn", "client_id", "client_id", "client_id"),
            ("desire2learn", "groups_enabled", "off", False),
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
            ("hypothesis", "notes", "  NOTES ", "NOTES"),
            ("hypothesis", "notes", "", None),
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

    @pytest.mark.parametrize(
        "setting,sub_setting", (("desire2learn", "client_secret"),)
    )
    def test_update_instance_saves_secret_settings(
        self,
        application_instance_service,
        aes_service,
        pyramid_request,
        setting,
        sub_setting,
    ):
        pyramid_request.matchdict["consumer_key"] = sentinel.consumer_key
        pyramid_request.params[f"{setting}.{sub_setting}"] = "SECRET"
        # This fixture returns a real AI, let's use a mock for this test
        application_instance_service.get_by_consumer_key.return_value = create_autospec(
            ApplicationInstance
        )

        AdminApplicationInstanceViews(pyramid_request).update_instance()

        ai = application_instance_service.get_by_consumer_key.return_value
        ai.settings.set_secret.assert_called_once_with(
            aes_service, setting, sub_setting, "SECRET"
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
    def ai_new_params_v13(self, ai_new_params_v11):
        ai_new_params_v11["deployment_id"] = "  22222  "
        ai_new_params_v11["lti_registration_id"] = "  54321 "
        return ai_new_params_v11

    @pytest.fixture
    def ai_new_params_v11(self, pyramid_request):
        params = {
            "lms_url": "http://example.com",
            "email": "test@example.com",
            "developer_key": "DEVELOPER_KEY",
            "developer_secret": "DEVELOPER_SECRET",
            "organization_public_id": "   us.lms.org.ID   ",
        }
        pyramid_request.POST = pyramid_request.params = params
        return params

    @pytest.fixture
    def application_instance_lti_13(self, application_instance, db_session):
        lti_registration = factories.LTIRegistration()
        # Get a valid ID for the registration
        db_session.flush()
        application_instance.lti_registration_id = lti_registration.id
        application_instance.deployment_id = "ID"

        return application_instance

    @pytest.fixture
    def with_upgrade_form(self, pyramid_request, application_instance):
        pyramid_request.POST = pyramid_request.params = {
            "lms_url": "http://lms-url.com",
            "email": "test@email.com",
            "deployment_id": "DEPLOYMENT_ID",
            "consumer_key": application_instance.consumer_key,
        }

        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminApplicationInstanceViews(pyramid_request)
