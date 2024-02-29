# pylint:disable=invalid-name
from lms.product.canvas import Canvas
from lms.services import JSTORService, VitalSourceService, YouTubeService
from dataclasses import dataclass, asdict


@dataclass
class APICallInfo:
    path: str
    authUrl: str | None
    data: dict | None = None


@dataclass
class Config:
    enabled: bool = False
    pagesEnabled: bool = False

    listFiles: APICallInfo | None = None
    listPages: APICallInfo | None = None


class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def lms_config(cls, request, product) -> dict:
        config = Config()
        if request.product.family != product.family:
            return asdict(config)

        config.enabled = product.settings.files_enabled
        config.pagesEnabled = product.settings.pages_enabled

        auth_url = (
            request.route_url(product.route.oauth2_authorize)
            if product.route.oauth2_authorize
            else None
        )
        course_id = request.lti_params.get("context_id")
        if config.enabled:
            config.listFiles = APICallInfo(
                path=request.route_path("api.courses.files.list", course_id=course_id),
                authUrl=auth_url,
            )

        return asdict(config)

    @classmethod
    def canvas_config(cls, request, application_instance):
        """Get Canvas files config."""

        files_enabled = application_instance.settings.get("canvas", "files_enabled")
        pages_enabled = application_instance.settings.get("canvas", "pages_enabled")

        course_id = request.lti_params.get("custom_canvas_course_id")
        config = {
            "enabled": files_enabled,
            "pagesEnabled": pages_enabled,
            "foldersEnabled": application_instance.settings.get(
                "canvas", "folders_enabled"
            ),
            "listFiles": {
                "authUrl": request.route_url(Canvas.route.oauth2_authorize),
                "path": request.route_path(
                    "api.courses.files.list", course_id=course_id
                ),
            },
        }

        if pages_enabled:
            config["listPages"] = {
                "authUrl": request.route_url(Canvas.route.oauth2_authorize),
                "path": request.route_path(
                    "canvas_api.courses.pages.list", course_id=course_id
                ),
            }

        return config

    @classmethod
    def google_files_config(cls, request, application_instance):
        """Get Google file picker config."""
        enabled = application_instance.settings.get(
            "google_drive", "files_enabled", default=True
        )
        if not enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "clientId": request.registry.settings["google_client_id"],
            "developerKey": request.registry.settings["google_developer_key"],
            # Get the URL of the top-most page that the LMS app is running in.
            # The frontend has to pass this to Google Picker, otherwise Google
            # Picker refuses to launch in an iframe.
            "origin": request.lti_params.get(
                "custom_canvas_api_domain", application_instance.lms_url
            ),
        }

    @classmethod
    def microsoft_onedrive(cls, request, application_instance):
        enabled = application_instance.settings.get(
            "microsoft_onedrive", "files_enabled", default=True
        )
        if not enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "clientId": request.registry.settings["onedrive_client_id"],
            "redirectURI": request.route_url("onedrive.filepicker.redirect_uri"),
        }

    @classmethod
    def vitalsource_config(cls, request, _application_instance):
        """Get VitalSource config."""

        svc = request.find_service(VitalSourceService)
        return {
            "enabled": svc.enabled,
            "pageRangesEnabled": svc.page_ranges_enabled,
        }

    @classmethod
    def jstor_config(cls, request, _application_instance):
        """Get JSTOR config."""

        return {"enabled": request.find_service(JSTORService).enabled}

    @classmethod
    def youtube_config(cls, request, _application_instance):
        return {"enabled": request.find_service(YouTubeService).enabled}
