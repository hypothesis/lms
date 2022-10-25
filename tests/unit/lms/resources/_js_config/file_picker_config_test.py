from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.product import Product
from lms.resources._js_config import FilePickerConfig


class TestFilePickerConfig:
    @pytest.mark.parametrize("files_enabled", [False, True])
    def test_blackboard_config(
        self, pyramid_request, application_instance, files_enabled
    ):

        pyramid_request.lti_params["context_id"] = "COURSE_ID"
        application_instance.settings.set("blackboard", "files_enabled", files_enabled)

        config = FilePickerConfig.blackboard_config(
            pyramid_request, application_instance
        )

        expected_config = {"enabled": files_enabled}

        if files_enabled:
            expected_config["listFiles"] = {
                "authUrl": "http://example.com/api/blackboard/oauth/authorize",
                "path": "/api/blackboard/courses/COURSE_ID/files",
            }

        assert config == expected_config

    @pytest.mark.usefixtures("with_is_canvas")
    def test_canvas_config(self, pyramid_request, application_instance):
        pyramid_request.lti_params["custom_canvas_course_id"] = "COURSE_ID"

        config = FilePickerConfig.canvas_config(pyramid_request, application_instance)

        expected_config = {
            "enabled": Any(),
            "listFiles": {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/files",
            },
        }

        assert config == expected_config

    @pytest.mark.parametrize(
        "missing_value",
        (None, "course_id", "developer_key"),
    )
    @pytest.mark.usefixtures("canvas_files_enabled")
    def test_canvas_config_enabled(
        self, pyramid_request, application_instance, missing_value
    ):
        if missing_value == "course_id":
            pyramid_request.params.pop("custom_canvas_course_id")
        elif missing_value == "developer_key":
            application_instance.developer_key = None

        config = FilePickerConfig.canvas_config(pyramid_request, application_instance)

        assert config["enabled"] != missing_value

    @pytest.mark.parametrize(
        "origin_from", (None, "custom_canvas_api_domain", "lms_url")
    )
    def test_google_files_config(
        self, pyramid_request, application_instance, origin_from
    ):
        if origin_from == "custom_canvas_api_domain":
            pyramid_request.lti_params["custom_canvas_api_domain"] = sentinel.origin
        elif origin_from == "lms_url":
            application_instance.lms_url = sentinel.origin

        config = FilePickerConfig.google_files_config(
            pyramid_request, application_instance
        )

        assert config == {
            "clientId": "fake_client_id",
            "developerKey": "fake_developer_key",
            "origin": sentinel.origin if origin_from else None,
        }

    @pytest.mark.parametrize("enabled", (True, False))
    def test_microsoft_onedrive(self, pyramid_request, application_instance, enabled):
        pyramid_request.registry.settings["onedrive_client_id"] = sentinel.client_id
        application_instance.settings.set(
            "microsoft_onedrive", "files_enabled", enabled
        )

        config = FilePickerConfig.microsoft_onedrive(
            pyramid_request, application_instance
        )

        expected = {"enabled": enabled}
        if enabled:
            expected["clientId"] = sentinel.client_id
            expected["redirectURI"] = pyramid_request.route_url(
                "onedrive.filepicker.redirect_uri"
            )

        assert config == expected

    def test_vitalsource_config(self, pyramid_request, vitalsource_service):
        config = FilePickerConfig.vitalsource_config(
            pyramid_request, sentinel.application_instance
        )

        assert config == {"enabled": vitalsource_service.enabled}

    @pytest.mark.parametrize("enabled", (True, False))
    def test_jstor_config(self, pyramid_request, jstor_service, enabled):
        jstor_service.enabled = enabled

        config = FilePickerConfig.jstor_config(
            pyramid_request, sentinel.application_instance
        )

        assert config == {"enabled": enabled}

    @pytest.fixture
    @pytest.mark.usefixtures("with_is_canvas")
    def canvas_files_enabled(self, pyramid_request, application_instance):
        pyramid_request.params["custom_canvas_course_id"] = sentinel.course_id
        application_instance.developer_key = sentinel.developer_key

    @pytest.fixture
    def with_is_canvas(self, pyramid_request):
        pyramid_request.product.family = Product.Family.CANVAS

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.lms_url = None

        return application_instance
