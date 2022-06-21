from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.resources._js_config import FilePickerConfig


class TestFilePickerConfig:
    @pytest.mark.parametrize(
        "files_enabled,groups_enabled",
        [
            (False, False),
            (True, False),
            (False, True),
            (True, True),
        ],
    )
    def test_blackboard_config(
        self,
        context,
        pyramid_request,
        application_instance,
        files_enabled,
        groups_enabled,
    ):

        context.lti_params["context_id"] = "COURSE_ID"
        application_instance.settings.set("blackboard", "files_enabled", files_enabled)
        application_instance.settings.set(
            "blackboard", "groups_enabled", groups_enabled
        )

        config = FilePickerConfig.blackboard_config(
            context, pyramid_request, application_instance
        )

        expected_config = {
            "enabled": files_enabled,
            "groupsEnabled": groups_enabled,
        }

        if files_enabled:
            expected_config["listFiles"] = {
                "authUrl": "http://example.com/api/blackboard/oauth/authorize",
                "path": "/api/blackboard/courses/COURSE_ID/files",
            }

        if groups_enabled:
            expected_config["listGroupSets"] = {
                "authUrl": "http://example.com/api/blackboard/oauth/authorize",
                "path": "/api/blackboard/courses/COURSE_ID/group_sets",
            }

        assert config == expected_config

    @pytest.mark.usefixtures("with_is_canvas")
    @pytest.mark.parametrize(
        "groups_enabled",
        [
            False,
            True,
        ],
    )
    def test_canvas_config(
        self, context, pyramid_request, application_instance, groups_enabled
    ):
        context.lti_params["custom_canvas_course_id"] = "COURSE_ID"
        application_instance.settings.set("canvas", "groups_enabled", groups_enabled)

        config = FilePickerConfig.canvas_config(
            context, pyramid_request, application_instance
        )

        expected_config = {
            "enabled": Any(),
            "groupsEnabled": groups_enabled,
            "listFiles": {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/files",
            },
        }

        if groups_enabled:
            expected_config["listGroupSets"] = {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/group_sets",
            }

        assert config == expected_config

    @pytest.mark.parametrize(
        "missing_value",
        (None, "course_id", "developer_key"),
    )
    @pytest.mark.usefixtures("canvas_files_enabled")
    def test_canvas_config_enabled(
        self, context, pyramid_request, application_instance, missing_value
    ):
        if missing_value == "course_id":
            pyramid_request.params.pop("custom_canvas_course_id")
        elif missing_value == "developer_key":
            application_instance.developer_key = None

        config = FilePickerConfig.canvas_config(
            context, pyramid_request, application_instance
        )

        assert config["enabled"] != missing_value

    @pytest.mark.parametrize("origin_from", ("custom_canvas_api_domain", "lms_url"))
    def test_google_files_config(
        self, context, pyramid_request, application_instance, origin_from
    ):
        if origin_from == "custom_canvas_api_domain":
            context.lti_params["custom_canvas_api_domain"] = origin_from
        elif origin_from == "lms_url":
            application_instance.lms_url = origin_from

        config = FilePickerConfig.google_files_config(
            context, pyramid_request, application_instance
        )

        assert config == {
            "clientId": "fake_client_id",
            "developerKey": "fake_developer_key",
            "origin": origin_from,
        }

    @pytest.mark.parametrize("enabled", (True, False))
    def test_microsoft_onedrive(
        self, context, pyramid_request, application_instance, enabled
    ):
        pyramid_request.registry.settings["onedrive_client_id"] = sentinel.client_id
        application_instance.settings.set(
            "microsoft_onedrive", "files_enabled", enabled
        )

        config = FilePickerConfig.microsoft_onedrive(
            context, pyramid_request, application_instance
        )

        expected = {"enabled": enabled}
        if enabled:
            expected["clientId"] = sentinel.client_id
            expected["redirectURI"] = pyramid_request.route_url(
                "onedrive.filepicker.redirect_uri"
            )

        assert config == expected

    @pytest.mark.parametrize("enabled", (True, False))
    def test_vital_source_config(
        self, context, pyramid_request, application_instance, enabled
    ):
        application_instance.settings.set("vitalsource", "enabled", enabled)

        config = FilePickerConfig.vital_source_config(
            context, pyramid_request, application_instance
        )

        assert config == {"enabled": enabled}

    @pytest.mark.parametrize("enabled", (True, False))
    def test_jstor_config(self, pyramid_request, jstor_service, enabled):
        jstor_service.enabled = enabled

        config = FilePickerConfig.jstor_config(
            sentinel.context, pyramid_request, sentinel.application_instance
        )

        assert config == {"enabled": enabled}

    @pytest.fixture
    def canvas_files_enabled(self, context, pyramid_request, application_instance):
        context.is_canvas = True
        pyramid_request.params["custom_canvas_course_id"] = sentinel.course_id
        application_instance.developer_key = sentinel.developer_key

    @pytest.fixture
    def with_is_canvas(self, context):
        context.is_canvas = True

    @pytest.fixture
    def context(self, pyramid_request):
        return create_autospec(
            LTILaunchResource,
            spec_set=True,
            instance=True,
            is_canvas=False,
            lti_params=LTIParams(pyramid_request.params),
        )
