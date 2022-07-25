from lms.product import Product
from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.services import JSTORService, VitalSourceService


class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def blackboard_config(cls, request, application_instance):
        """Get Blackboard files config."""
        files_enabled = application_instance.settings.get("blackboard", "files_enabled")
        groups_enabled = application_instance.settings.get(
            "blackboard", "groups_enabled"
        )

        auth_url = request.route_url(Blackboard.route.oauth2_authorize)
        course_id = request.lti_params.get("context_id")

        config = {
            "enabled": files_enabled,
            "groupsEnabled": groups_enabled,
        }

        if files_enabled:
            config["listFiles"] = {
                "authUrl": auth_url,
                "path": request.route_path(
                    "blackboard_api.courses.files.list", course_id=course_id
                ),
            }

        if groups_enabled:
            config["listGroupSets"] = {
                "authUrl": auth_url,
                "path": request.route_path(
                    "blackboard_api.courses.group_sets.list", course_id=course_id
                ),
            }

        return config

    @classmethod
    def canvas_config(cls, request, application_instance):
        """Get Canvas files config."""

        enabled = (request.product.family == Product.Family.CANVAS) and (
            "custom_canvas_course_id" in request.lti_params
            and application_instance.developer_key is not None
        )
        groups_enabled = application_instance.settings.get("canvas", "groups_enabled")

        auth_url = request.route_url(Canvas.route.oauth2_authorize)
        course_id = request.lti_params.get("custom_canvas_course_id")

        config = {
            "enabled": enabled,
            "groupsEnabled": groups_enabled,
            "listFiles": {
                "authUrl": auth_url,
                "path": request.route_path(
                    "canvas_api.courses.files.list", course_id=course_id
                ),
            },
        }

        if groups_enabled:
            config["listGroupSets"] = {
                "authUrl": auth_url,
                "path": request.route_path(
                    "canvas_api.courses.group_sets.list", course_id=course_id
                ),
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
