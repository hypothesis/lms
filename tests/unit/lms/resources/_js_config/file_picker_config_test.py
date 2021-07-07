from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.resources import LTILaunchResource
from lms.resources._js_config import FilePickerConfig


class TestFilePickerConfig:
    def test_blackboard_config(self, context, pyramid_request, application_instance):
        pyramid_request.params["context_id"] = "COURSE_ID"
        application_instance.settings.set(
            "blackboard", "files_enabled", sentinel.enabled
        )

        config = FilePickerConfig.blackboard_config(
            context, pyramid_request, application_instance
        )

        assert config == {
            "enabled": sentinel.enabled,
            "listFiles": {
                "authUrl": "http://example.com/api/blackboard/oauth/authorize",
                "path": "/api/blackboard/courses/COURSE_ID/files",
            },
        }

    def test_canvas_config(self, context, pyramid_request, application_instance):
        pyramid_request.params["custom_canvas_course_id"] = "COURSE_ID"

        config = FilePickerConfig.canvas_config(
            context, pyramid_request, application_instance
        )

        assert config == {
            "enabled": Any(),
            "groupsEnabled": False,
            "listFiles": {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/files",
            },
            "listGroupSets": {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/group_sets",
            },
            "ltiLaunchUrl": "http://example.com/lti_launches",
        }

    @pytest.mark.parametrize(
        "missing_value",
        (None, "is_canvas", "course_id", "developer_key"),
    )
    @pytest.mark.usefixtures("canvas_files_enabled")
    def test_canvas_config_enabled(
        self, context, pyramid_request, application_instance, missing_value
    ):
        if missing_value == "is_canvas":
            context.is_canvas = False
        elif missing_value == "course_id":
            pyramid_request.params.pop("custom_canvas_course_id")
        elif missing_value == "developer_key":
            application_instance.developer_key = None

        config = FilePickerConfig.canvas_config(
            context, pyramid_request, application_instance
        )

        assert config["enabled"] != missing_value

    @pytest.mark.parametrize(
        "origin_from", (None, "custom_canvas_api_domain", "lms_url")
    )
    def test_google_files_config(
        self, context, pyramid_request, application_instance, origin_from
    ):
        if origin_from == "custom_canvas_api_domain":
            context.custom_canvas_api_domain = sentinel.origin
        elif origin_from == "lms_url":
            application_instance.lms_url = sentinel.origin

        config = FilePickerConfig.google_files_config(
            context, pyramid_request, application_instance
        )

        assert config == {
            "clientId": "fake_client_id",
            "developerKey": "fake_developer_key",
            "origin": sentinel.origin if origin_from else None,
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

        assert config == expected

    def test_vital_source_config(self, context, pyramid_request, application_instance):
        pyramid_request.feature.return_value = sentinel.enabled

        config = FilePickerConfig.vital_source_config(
            context, pyramid_request, application_instance
        )

        assert config == {"enabled": sentinel.enabled}
        pyramid_request.feature.assert_called_once_with("vitalsource")

    @pytest.fixture
    def canvas_files_enabled(self, context, pyramid_request, application_instance):
        context.is_canvas = True
        pyramid_request.params["custom_canvas_course_id"] = sentinel.course_id
        application_instance.developer_key = sentinel.developer_key

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.lms_url = None

        return application_instance

    @pytest.fixture
    def context(self):
        return create_autospec(
            LTILaunchResource,
            spec_set=True,
            instance=True,
            is_canvas=False,
            canvas_sections_enabled=False,
            canvas_groups_enabled=False,
            custom_canvas_api_domain=None,
        )
