from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.d2l import D2L
from lms.services import JSTORService, VitalSourceService


class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def d2l_config(cls, request, _application_instance):
        """Get D2L files config."""
        files_enabled = (
            request.product.family == D2L.family
            and request.product.settings.files_enabled
        )
        config = {"enabled": files_enabled}
        if files_enabled:
            config["listFiles"] = {
                "authUrl": request.route_url(D2L.route.oauth2_authorize),
                "path": request.route_path(
                    "d2l_api.courses.files.list",
                    course_id=request.lti_params.get("context_id"),
                ),
            }

        return config

    @classmethod
    def blackboard_config(cls, request, application_instance):
        """Get Blackboard files config."""
        files_enabled = application_instance.settings.get("blackboard", "files_enabled")

        config = {"enabled": files_enabled}
        if files_enabled:
            config["listFiles"] = {
                "authUrl": request.route_url(Blackboard.route.oauth2_authorize),
                "path": request.route_path(
                    "blackboard_api.courses.files.list",
                    course_id=request.lti_params.get("context_id"),
                ),
            }

        return config

    @classmethod
    def canvas_config(cls, request, application_instance):
        """Get Canvas files config."""

        files_enabled = application_instance.settings.get("canvas", "files_enabled")

        course_id = request.lti_params.get("custom_canvas_course_id")
        config = {
            "enabled": files_enabled,
            "listFiles": {
                "authUrl": request.route_url(Canvas.route.oauth2_authorize),
                "path": request.route_path(
                    "canvas_api.courses.files.list", course_id=course_id
                ),
            },
        }

        return config

    @classmethod
    def google_files_config(cls, request, application_instance):
        """Get Google file picker config."""

        return {
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

        return {"enabled": request.find_service(VitalSourceService).enabled}

    @classmethod
    def jstor_config(cls, request, _application_instance):
        """Get JSTOR config."""

        return {"enabled": request.find_service(JSTORService).enabled}
