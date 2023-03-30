from lms.content_source.content_source import ContentSource
from lms.content_source.models import FileDisplayConfig
from lms.product.canvas.product import Canvas


class CanvasFiles(ContentSource):
    url_scheme = "canvas"
    config_key = "canvas"

    def __init__(self, request):
        self._request = request

    def is_enabled(self, application_instance):
        return application_instance.settings.get("canvas", "files_enabled")

    def get_picker_config(self, application_instance):
        course_id = self._request.lti_params.get("custom_canvas_course_id")

        return {
            "listFiles": {
                "authUrl": self._request.route_url(Canvas.route.oauth2_authorize),
                "path": self._request.route_path(
                    "canvas_api.courses.files.list", course_id=course_id
                ),
            },
        }

    def get_file_display_config(self, document_url) -> FileDisplayConfig:
        return FileDisplayConfig(
            callback={
                "authUrl": self._request.route_url(Canvas.route.oauth2_authorize),
                "path": self._request.route_path(
                    "canvas_api.files.via_url",
                    resource_link_id=self._request.lti_params["resource_link_id"],
                ),
            }
        )

    @classmethod
    def factory(cls, _config, request):
        return CanvasFiles(request=request)
