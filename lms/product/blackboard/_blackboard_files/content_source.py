from lms.content_source.content_source import ContentSource
from lms.content_source.models import FileDisplayConfig
from lms.product.blackboard.product import Blackboard


class BlackboardFiles(ContentSource):
    url_scheme = "blackboard"
    config_key = "blackboard"

    def __init__(self, request):
        self._request = request

    def is_enabled(self, application_instance):
        return application_instance.settings.get("blackboard", "files_enabled")

    def get_picker_config(self, application_instance) -> dict:
        return {
            "authUrl": self._request.route_url(Blackboard.route.oauth2_authorize),
            "path": self._request.route_path(
                "blackboard_api.courses.files.list",
                course_id=self._request.lti_params.get("context_id"),
            ),
        }

    def get_file_display_config(self, document_url):
        return FileDisplayConfig(
            callback={
                "authUrl": self._request.route_url(Blackboard.route.oauth2_authorize),
                "path": self._request.route_path(
                    "blackboard_api.files.via_url",
                    course_id=self._request.lti_params["context_id"],
                    _query={"document_url": document_url},
                ),
            }
        )

    @classmethod
    def factory(cls, _config, request):
        return BlackboardFiles(request=request)
