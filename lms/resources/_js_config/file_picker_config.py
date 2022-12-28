from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.d2l import D2L
from lms.services import JSTORService, VitalSourceService


class FilePickerConfig:
    """Config generation for specific file pickers."""

    @classmethod
    def d2l_config(cls, request, application_instance):
        """Get D2L files config."""
        return cls._lms_files_config(
            request, D2L, application_instance, request.lti_params.get("context_id")
        )

    @classmethod
    def blackboard_config(cls, request, application_instance):
        """Get Blackboard files config."""
        return cls._lms_files_config(
            request,
            Blackboard,
            application_instance,
            request.lti_params.get("context_id"),
        )

    @classmethod
    def canvas_config(cls, request, application_instance):
        """Get Canvas files config."""

        return cls._lms_files_config(
            request,
            Canvas,
            application_instance,
            request.lti_params.get("custom_canvas_course_id"),
        )

    @classmethod
    def _lms_files_config(cls, request, product, application_instance, course_id):
        """Get the config for the current LMS file storage."""
        product = product.from_request(request, dict(application_instance.settings))

        files_enabled = (
            request.product.family == product.family and product.settings.files_enabled
        )

        config = {"enabled": files_enabled}
        if files_enabled:
            config["listFiles"] = {
                "authUrl": request.route_url(product.route.oauth2_authorize),
                "path": request.route_path(
                    product.route.list_course_files, course_id=course_id
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
