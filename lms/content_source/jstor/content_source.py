from lms.content_source.content_source import ContentSource
from lms.content_source.models import FileDisplayConfig
from lms.services import JSTORService


class JSTOR(ContentSource):
    url_scheme = "jstor"
    config_key = "jstor"

    def __init__(self, request, service: JSTORService):
        self._request = request
        self._service = service

    def is_enabled(self, application_instance):
        return self._service.enabled

    def get_file_display_config(self, document_url):
        document_url = self._service.via_url(self._request, document_url)

        return FileDisplayConfig(
            direct_url=document_url,
            banner=FileDisplayConfig.BannerConfig(
                source="jstor", item_id=document_url.replace("jstor://", "")
            ),
        )

    @classmethod
    def factory(cls, _context, request):
        return JSTOR(request=request, service=request.find_service(JSTORService))
