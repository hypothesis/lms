from typing import Optional

from lms.content_source.content_source import ContentSource
from lms.content_source.models import FileDisplayConfig
from lms.product import Product
from lms.product.d2l import D2L


class D2LFiles(ContentSource):
    url_scheme = "d2l"
    config_key = "d2l"
    family = Product.Family.D2L

    def __init__(self, request):
        self._request = request

    def is_enabled(self, application_instance):
        return self._request.product.settings.files_enabled

    def get_picker_config(self, application_instance) -> Optional[dict]:
        return {
            "listFiles": {
                "authUrl": self._request.route_url(D2L.route.oauth2_authorize),
                "path": self._request.route_path(
                    "d2l_api.courses.files.list",
                    course_id=self._request.lti_params.get("context_id"),
                ),
            }
        }

    def get_file_display_config(self, document_url) -> FileDisplayConfig:
        return FileDisplayConfig(
            callback={
                "authUrl": self._request.route_url(D2L.route.oauth2_authorize),
                "path": self._request.route_path(
                    "d2l_api.courses.files.via_url",
                    course_id=self._request.lti_params["context_id"],
                    _query={"document_url": document_url},
                ),
            }
        )

    @classmethod
    def factory(cls, _config, request):
        return D2LFiles(request=request)
