from unittest.mock import patch, sentinel

import pytest
from pyramid.httpexceptions import HTTPClientError, HTTPFound, HTTPNotFound
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

REDIRECT_TO_UPGRADE_AI = Any.instance_of(HTTPFound).with_attrs(
    {"location": Any.string.containing("/admin/instance/upgrade")}
)


@pytest.mark.usefixtures(
    "application_instance_service",
    "lti_registration_service",
    "organization_service",
    "aes_service",
)
class TestAdminApplicationInstanceViews:
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
            name="NAME",
            lms_url="http://example.com",
            email="test@example.com",
            deployment_id="22222",
            developer_key="DEVELOPER_KEY",
            developer_secret="DEVELOPER_SECRET",
            organization_public_id="us.lms.org.ID",
            lti_registration_id=54321,
        )
        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": Any.string.containing("/admin/instance/12345")}
        )

    @pytest.mark.usefixtures("ai_new_params_v11")
    def test_new_instance_callback_v11(self, views):
        response = views.new_instance_callback()

        assert response == Any.instance_of(HTTPFound).with_attrs(
            {"location": Any.string.containing("/admin/instance/")}
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
        ("name", None),
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
        self, views, pyramid_request, ai_from_matchdict, application_instance_service
    ):
        pyramid_request.params["org_public_id"] = "PUBLIC_ID"

        response = views.move_application_instance_org()

        application_instance_service.update_application_instance.assert_called_once_with(
            ai_from_matchdict, organization_public_id="PUBLIC_ID"
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=ai_from_matchdict.id)
        )

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_move_application_instance_org_invalid_organization_id(
        self, views, pyramid_request, application_instance_service
    ):
        pyramid_request.params["org_public_id"] = "PUBLIC_ID"
        application_instance_service.update_application_instance.side_effect = (
            ValidationError(messages=sentinel.messages)
        )

        response = views.move_application_instance_org()

        assert pyramid_request.session.peek_flash("validation")
        assert response == temporary_redirect_to(
            pyramid_request.route_url(
                "admin.instance",
                id_=application_instance_service.get_by_id.return_value.id,
            )
        )

    @pytest.mark.usefixtures("with_lti_13_ai")
    def test_downgrade_instance(self, views, pyramid_request, ai_from_matchdict):
        response = views.downgrade_instance()

        assert not ai_from_matchdict.lti_registration_id
        assert not ai_from_matchdict.deployment_id
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=ai_from_matchdict.id)
        )

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_downgrade_instance_no_lti13(self, views, pyramid_request):
        views.downgrade_instance()

        assert pyramid_request.session.peek_flash("errors")

    @pytest.mark.usefixtures("with_lti_13_ai")
    def test_downgrade_instance_no_consumer_key(
        self, views, pyramid_request, ai_from_matchdict
    ):
        ai_from_matchdict.consumer_key = None

        views.downgrade_instance()

        assert pyramid_request.session.peek_flash("errors")

    @pytest.mark.parametrize("lti_registration_id", ("123", "  123   "))
    def test_upgrade_instance_start(
        self, views, pyramid_request, lti_registration_service, lti_registration_id
    ):
        pyramid_request.params = {
            "lti_registration_id": lti_registration_id,
            "key_1": "value_1",
            "key_2": "value_2",
        }

        response = views.upgrade_instance_start()

        lti_registration_service.get_by_id.assert_called_once_with("123")
        assert response == dict(
            pyramid_request.params,
            lti_registration=lti_registration_service.get_by_id.return_value,
        )

    def test_upgrade_instance_start_with_no_registration_id(
        self, views, pyramid_request
    ):
        pyramid_request.params.pop("lti_registration_id", None)

        with pytest.raises(HTTPClientError):
            views.upgrade_instance_start()

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback(
        self,
        views,
        pyramid_request,
        application_instance,
        application_instance_service,
        lti_registration_service,
    ):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        assert not application_instance.lti_registration

        response = views.upgrade_instance_callback()

        application_instance_service.get_by_consumer_key.assert_called_once_with(
            application_instance.consumer_key
        )
        assert application_instance.lti_registration == lti_registration
        assert (
            application_instance.deployment_id
            == pyramid_request.params["deployment_id"]
        )
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=application_instance.id)
        )

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback_with_no_deployment_id(
        self, views, pyramid_request
    ):
        del pyramid_request.POST["deployment_id"]

        assert views.upgrade_instance_callback() == REDIRECT_TO_UPGRADE_AI

    @pytest.mark.usefixtures("with_upgrade_form", "with_lti_13_ai")
    def test_upgrade_instance_callback_already_upgraded(self, views):
        assert views.upgrade_instance_callback() == REDIRECT_TO_UPGRADE_AI

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback_with_duplicate(
        self, views, db_session, lti_registration_service
    ):
        lti_registration = factories.LTIRegistration()
        lti_registration_service.get_by_id.return_value = lti_registration
        factories.ApplicationInstance(
            lti_registration=lti_registration, deployment_id="DEPLOYMENT_ID"
        )

        response = views.upgrade_instance_callback()

        assert response == REDIRECT_TO_UPGRADE_AI

        # Show that the DB connection has not been permanently broken. This
        # would cause us to fail completely when trying to present the error.
        # We are checking we do _not_ raise `PendingRollbackError` here.
        db_session.query(ApplicationInstance).all()

    @pytest.mark.usefixtures("with_upgrade_form")
    def test_upgrade_instance_callback_with_non_existent_instance(
        self, views, application_instance_service
    ):
        application_instance_service.get_by_consumer_key.side_effect = (
            ApplicationInstanceNotFound
        )

        assert views.upgrade_instance_callback() == REDIRECT_TO_UPGRADE_AI

    def test_search_start(self, views):
        assert not views.search_start()

    def test_search(self, pyramid_request, application_instance_service, views):
        pyramid_request.params = pyramid_request.POST = {
            "id": "1",
            "name": "NAME",
            "consumer_key": "CONSUMER_KEY",
            "issuer": "ISSUER",
            "client_id": "CLIENT_ID",
            "deployment_id": "DEPLOYMENT_ID",
            "tool_consumer_instance_guid": "TOOL_CONSUMER_INSTANCE_GUID",
        }

        response = views.search_callback()

        application_instance_service.search.assert_called_once_with(
            id_="1",
            name="NAME",
            consumer_key="CONSUMER_KEY",
            issuer="ISSUER",
            client_id="CLIENT_ID",
            deployment_id="DEPLOYMENT_ID",
            tool_consumer_instance_guid="TOOL_CONSUMER_INSTANCE_GUID",
        )
        assert response == {
            "instances": application_instance_service.search.return_value
        }

    def test_search_callback_invalid(self, views, pyramid_request):
        pyramid_request.POST = {"id": "not a number"}

        assert not views.search_callback()
        assert pyramid_request.session.peek_flash

    def test_show_instance_id(self, views, ai_from_matchdict):
        response = views.show_instance()

        assert response["instance"].id == ai_from_matchdict.id

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_show_instance_not_found(self, views, application_instance_service):
        application_instance_service.get_by_id.side_effect = ApplicationInstanceNotFound

        with pytest.raises(HTTPNotFound):
            views.show_instance()

    @pytest.mark.usefixtures("with_minimal_fields_for_update")
    def test_update_instance(self, views, pyramid_request, ai_from_matchdict):
        response = views.update_instance()

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=ai_from_matchdict.id)
        )

    def test_update_application_instance(
        self, views, pyramid_request, ai_from_matchdict, application_instance_service
    ):
        pyramid_request.params = pyramid_request.POST = {
            "name": "  NAME  ",
            "lms_url": "http://example.com",
            "deployment_id": " DEPLOYMENT_ID  ",
            "developer_key": "  DEVELOPER KEY  ",
            "developer_secret": " DEVELOPER SECRET  ",
        }

        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            ai_from_matchdict,
            name="NAME",
            lms_url="http://example.com",
            deployment_id="DEPLOYMENT_ID",
            developer_key="DEVELOPER KEY",
            developer_secret="DEVELOPER SECRET",
        )

    @pytest.mark.usefixtures("with_minimal_fields_for_update")
    def test_update_application_instance_with_minimal_arguments(
        self, views, ai_from_matchdict, application_instance_service
    ):
        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            ai_from_matchdict,
            name="NAME",
            lms_url="",
            deployment_id="",
            developer_key="",
            developer_secret="",
        )

    @pytest.mark.usefixtures("with_minimal_fields_for_update", "ai_from_matchdict")
    @pytest.mark.parametrize(
        "param,bad_value", (("lms_url", "not_a_url"), ("name", None))
    )
    def test_update_application_instance_with_invalid_arguments(
        self, views, pyramid_request, application_instance_service, param, bad_value
    ):
        pyramid_request.params[param] = pyramid_request.POST[param] = bad_value

        views.update_instance()

        application_instance_service.update_application_instance.assert_not_called()

    @pytest.mark.usefixtures("with_minimal_fields_for_update")
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
        views,
        pyramid_request,
        ai_from_matchdict,
        setting,
        sub_setting,
        value,
        expected,
    ):
        pyramid_request.params[f"{setting}.{sub_setting}"] = value

        views.update_instance()

        assert ai_from_matchdict.settings.get(setting, sub_setting) == expected

    @pytest.mark.usefixtures("with_minimal_fields_for_update")
    @pytest.mark.parametrize(
        "setting,sub_setting", (("desire2learn", "client_secret"),)
    )
    def test_update_instance_saves_secret_settings(
        self,
        views,
        pyramid_request,
        ai_from_matchdict,
        aes_service,
        setting,
        sub_setting,
    ):
        pyramid_request.params[f"{setting}.{sub_setting}"] = "SECRET"

        with patch.object(ai_from_matchdict.settings, "set_secret"):
            views.update_instance()

            ai_from_matchdict.settings.set_secret.assert_called_once_with(
                aes_service, setting, sub_setting, "SECRET"
            )

    @pytest.mark.usefixtures("ai_from_matchdict")
    def test_update_instance_not_found(self, views, application_instance_service):
        application_instance_service.get_by_id.side_effect = ApplicationInstanceNotFound

        with pytest.raises(HTTPNotFound):
            views.update_instance()

    @pytest.fixture
    def ai_from_matchdict(
        self, pyramid_request, application_instance_service, application_instance
    ):
        pyramid_request.matchdict["id_"] = sentinel.id_
        application_instance_service.get_by_id.return_value = application_instance

        return application_instance

    @pytest.fixture
    def ai_new_params_v13(self, ai_new_params_v11):
        ai_new_params_v11["deployment_id"] = "  22222  "
        ai_new_params_v11["lti_registration_id"] = "  54321 "
        return ai_new_params_v11

    @pytest.fixture
    def ai_new_params_v11(self, pyramid_request):
        params = {
            "name": "  NAME  ",
            "lms_url": "http://example.com",
            "email": "test@example.com",
            "developer_key": "DEVELOPER_KEY",
            "developer_secret": "DEVELOPER_SECRET",
            "organization_public_id": "   us.lms.org.ID   ",
        }
        pyramid_request.POST = pyramid_request.params = params
        return params

    @pytest.fixture
    def with_lti_13_ai(self, application_instance, db_session):
        lti_registration = factories.LTIRegistration()
        # Get a valid ID for the registration
        db_session.flush()
        application_instance.lti_registration_id = lti_registration.id
        application_instance.deployment_id = "ID"

    @pytest.fixture
    def with_upgrade_form(self, pyramid_request, application_instance):
        pyramid_request.POST = pyramid_request.params = {
            "name": "NAME",
            "lms_url": "http://lms-url.com",
            "email": "test@email.com",
            "deployment_id": "DEPLOYMENT_ID",
            "consumer_key": application_instance.consumer_key,
        }

        return pyramid_request

    @pytest.fixture
    def with_minimal_fields_for_update(self, pyramid_request):
        pyramid_request.params = pyramid_request.POST = {"name": "NAME"}

    @pytest.fixture
    def views(self, pyramid_request):
        return AdminApplicationInstanceViews(pyramid_request)
