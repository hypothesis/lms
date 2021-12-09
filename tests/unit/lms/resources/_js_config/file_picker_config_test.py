from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

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
        blackboard_application_instance,
        files_enabled,
        groups_enabled,
    ):

        pyramid_request.params["context_id"] = "COURSE_ID"
        blackboard_application_instance.settings.set(
            "blackboard", "files_enabled", files_enabled
        )
        context.blackboard_groups_enabled = groups_enabled

        config = FilePickerConfig.blackboard_config(
            context, pyramid_request, blackboard_application_instance
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
        pyramid_request.params["custom_canvas_course_id"] = "COURSE_ID"
        context.canvas_groups_enabled = groups_enabled

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
    def blackboard_application_instance(self, application_instance):
        application_instance.tool_consumer_info_product_family_code = "BlackboardLearn"

        return application_instance

    @pytest.fixture
    def with_is_canvas(self, context):
        context.is_canvas = True

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
            blackboard_groups_enabled=False,
        )
