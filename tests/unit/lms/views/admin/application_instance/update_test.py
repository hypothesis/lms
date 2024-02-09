from unittest.mock import patch

import pytest

from lms.views.admin.application_instance.update import UpdateApplicationInstanceView
from tests.matchers import temporary_redirect_to


@pytest.mark.usefixtures("application_instance_service", "aes_service")
class TestUpdateApplicationInstanceView:
    @pytest.mark.usefixtures("with_minimal_fields_for_update")
    def test_update_instance(self, views, pyramid_request, ai_from_matchdict):
        response = views.update_instance()

        assert pyramid_request.session.peek_flash("messages")
        assert response == temporary_redirect_to(
            pyramid_request.route_url("admin.instance", id_=ai_from_matchdict.id)
        )

    @pytest.mark.parametrize(
        "setting,sub_setting,value,expected",
        (
            ("hypothesis", "notes", "  NOTES ", "NOTES"),
            ("hypothesis", "notes", "", None),
        ),
    )
    def test_update_application_instance(
        self,
        views,
        pyramid_request,
        ai_from_matchdict,
        application_instance_service,
        setting,
        sub_setting,
        value,
        expected,
    ):
        pyramid_request.params = pyramid_request.POST = {
            "name": "  NAME  ",
            "lms_url": "http://example.com",
            "deployment_id": " DEPLOYMENT_ID  ",
            "developer_key": "  DEVELOPER KEY  ",
            "developer_secret": " DEVELOPER SECRET  ",
        }
        pyramid_request.params[f"{setting}.{sub_setting}"] = value

        views.update_instance()

        application_instance_service.update_application_instance.assert_called_once_with(
            ai_from_matchdict,
            name="NAME",
            lms_url="http://example.com",
            deployment_id="DEPLOYMENT_ID",
            developer_key="DEVELOPER KEY",
            developer_secret="DEVELOPER SECRET",  # noqa: S106
        )
        assert ai_from_matchdict.settings.get(setting, sub_setting) == expected

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

    @pytest.mark.parametrize(
        "setting,sub_setting,value,expected",
        (
            # Tri-state boolean fields
            ("canvas", "groups_enabled", "true", True),
            ("canvas", "sections_enabled", "false", False),
            ("blackboard", "files_enabled", "none", None),
            ("blackboard", "groups_enabled", "false", False),
            ("desire2learn", "client_id", "client_id", "client_id"),
            ("desire2learn", "groups_enabled", "false", False),
            ("microsoft_onedrive", "files_enabled", "true", True),
            ("vitalsource", "enabled", "true", True),
            ("jstor", "enabled", "false", False),
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
        views,
        pyramid_request,
        ai_from_matchdict,
        setting,
        sub_setting,
        value,
        expected,
    ):
        pyramid_request.params[f"{setting}.{sub_setting}"] = value

        views.update_instance_settings()

        assert ai_from_matchdict.settings.get(setting, sub_setting) == expected

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
            views.update_instance_settings()

            ai_from_matchdict.settings.set_secret.assert_called_once_with(
                aes_service, setting, sub_setting, "SECRET"
            )

    @pytest.fixture
    def with_minimal_fields_for_update(self, pyramid_request):
        pyramid_request.params = pyramid_request.POST = {"name": "NAME"}

    @pytest.fixture
    def views(self, pyramid_request):
        return UpdateApplicationInstanceView(pyramid_request)
