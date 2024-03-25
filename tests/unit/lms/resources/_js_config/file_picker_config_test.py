from unittest.mock import sentinel

import pytest

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

    @pytest.mark.parametrize("files_enabled", [False, True])
    @pytest.mark.parametrize("pages_enabled", [False, True])
    def test_moodle_config(
        self, pyramid_request, application_instance, files_enabled, pages_enabled
    ):
        pyramid_request.lti_params["context_id"] = "COURSE_ID"
        application_instance.settings.set("moodle", "files_enabled", files_enabled)
        application_instance.settings.set("moodle", "pages_enabled", pages_enabled)

        config = FilePickerConfig.moodle_config(pyramid_request, application_instance)

        expected_config = {"enabled": files_enabled, "pagesEnabled": pages_enabled}

        if files_enabled:
            expected_config["listFiles"] = {
                "authUrl": None,
                "path": "/api/courses/COURSE_ID/files",
            }
        if pages_enabled:
            expected_config["listPages"] = {
                "authUrl": None,
                "path": "/api/moodle/courses/COURSE_ID/pages",
            }

        assert config == expected_config

    @pytest.mark.parametrize(
        "family,enabled,expected",
        [
            (Product.Family.BLACKBOARD, False, False),
            (Product.Family.BLACKBOARD, True, False),
            (Product.Family.D2L, False, False),
            (Product.Family.D2L, True, True),
        ],
    )
    def test_d2l_config(self, pyramid_request, family, enabled, expected):
        pyramid_request.lti_params["context_id"] = "COURSE_ID"
        pyramid_request.product.family = family
        pyramid_request.product.settings.files_enabled = enabled

        config = FilePickerConfig.d2l_config(
            pyramid_request, sentinel.application_instance
        )

        expected_config = {"enabled": expected}

        if expected:
            expected_config["listFiles"] = {
                "authUrl": "http://example.com/api/d2l/oauth/authorize",
                "path": "/api/courses/COURSE_ID/files",
            }

        assert config == expected_config

    @pytest.mark.usefixtures("with_canvas")
    @pytest.mark.parametrize("files_enabled", [False, True])
    @pytest.mark.parametrize("pages_enabled", [False, True])
    @pytest.mark.parametrize("folders_enabled", [False, True])
    def test_canvas_config(
        self,
        pyramid_request,
        application_instance,
        files_enabled,
        pages_enabled,
        folders_enabled,
    ):
        application_instance.settings.set("canvas", "files_enabled", files_enabled)
        application_instance.settings.set("canvas", "pages_enabled", pages_enabled)
        application_instance.settings.set("canvas", "folders_enabled", folders_enabled)
        pyramid_request.lti_params["custom_canvas_course_id"] = "COURSE_ID"

        config = FilePickerConfig.canvas_config(pyramid_request, application_instance)

        expected_config = {
            "enabled": files_enabled,
            "pagesEnabled": pages_enabled,
            "foldersEnabled": folders_enabled,
            "listFiles": {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/files",
            },
        }

        if pages_enabled:
            expected_config["listPages"] = {
                "authUrl": "http://example.com/api/canvas/oauth/authorize",
                "path": "/api/canvas/courses/COURSE_ID/pages",
            }

        assert config == expected_config

    @pytest.mark.parametrize("enabled", [True, False])
    def test_canvas_studio_config(self, pyramid_request, application_instance, enabled):
        application_instance.settings.set(
            "canvas_studio", "client_id", "some_id" if enabled else None
        )
        config = FilePickerConfig.canvas_studio_config(
            pyramid_request, application_instance
        )

        assert config["enabled"] is enabled

        if enabled:
            assert config["listMedia"] == {
                "authUrl": "http://example.com/api/canvas_studio/oauth/authorize",
                "path": "/api/canvas_studio/media",
            }

    @pytest.mark.parametrize("enabled", (True, False))
    @pytest.mark.parametrize(
        "origin_from", (None, "custom_canvas_api_domain", "lms_url")
    )
    def test_google_files_config(
        self, pyramid_request, application_instance, origin_from, enabled
    ):
        application_instance.settings.set("google_drive", "files_enabled", enabled)
        if origin_from == "custom_canvas_api_domain":
            pyramid_request.lti_params["custom_canvas_api_domain"] = sentinel.origin
        elif origin_from == "lms_url":
            application_instance.lms_url = sentinel.origin

        config = FilePickerConfig.google_files_config(
            pyramid_request, application_instance
        )

        expected = {"enabled": enabled}
        if enabled:
            expected["clientId"] = "fake_client_id"
            expected["developerKey"] = "fake_developer_key"
            expected["origin"] = sentinel.origin if origin_from else None

        assert config == expected

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

    def test_vitalsource_config(
        self, pyramid_request, vitalsource_service, application_instance
    ):
        config = FilePickerConfig.vitalsource_config(
            pyramid_request, application_instance
        )

        assert config == {
            "enabled": vitalsource_service.enabled,
        }

    @pytest.mark.parametrize("enabled", (True, False))
    def test_jstor_config(self, pyramid_request, jstor_service, enabled):
        jstor_service.enabled = enabled

        config = FilePickerConfig.jstor_config(
            pyramid_request, sentinel.application_instance
        )

        assert config == {"enabled": enabled}

    @pytest.mark.parametrize("enabled", (True, False))
    def test_youtube_config(self, pyramid_request, youtube_service, enabled):
        youtube_service.enabled = enabled

        config = FilePickerConfig.youtube_config(
            pyramid_request, sentinel.application_instance
        )

        assert config == {"enabled": enabled}

    @pytest.fixture
    def with_canvas(self, pyramid_request):
        pyramid_request.product.family = Product.Family.CANVAS

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.lms_url = None

        return application_instance
