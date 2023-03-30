from lms.content_source.content_source import ContentSource
from lms.content_source.models import FileDisplayConfig
from lms.services import VitalSourceService


class Vitalsource(ContentSource):
    url_scheme = "vitalsource"
    config_key = "vitalSource"

    def __init__(self, request, service: VitalSourceService):
        self._request = request
        self._service = service

    def is_enabled(self, application_instance):
        return self._service.enabled

    def get_file_display_config(self, document_url):
        if not self._service.sso_enabled:
            return FileDisplayConfig(
                direct_url=self._service.get_book_reader_url(document_url=document_url)
            )

        return FileDisplayConfig(
            callback={
                "path": self._request.route_url(
                    "vitalsource_api.launch_url",
                    _query={
                        "user_reference": self._service.get_user_reference(
                            self._request.lti_params
                        ),
                        "document_url": document_url,
                    },
                )
            }
        )

    @classmethod
    def factory(cls, _config, request):
        return Vitalsource(
            request=request, service=request.find_service(VitalSourceService)
        )
