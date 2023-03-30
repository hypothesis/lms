from typing import Optional

from lms.content_source.content_source import ContentSource


class GoogleFiles(ContentSource):
    url_scheme = None
    config_key = "google"

    def __init__(self, request, client_id, developer_key):
        self._request = request
        self._client_id = client_id
        self._developer_key = developer_key

    def get_picker_config(self, application_instance) -> Optional[dict]:
        return {
            "clientId": self._client_id,
            "developerKey": self._developer_key,
            # Get the URL of the top-most page that the LMS app is running in.
            # The frontend has to pass this to Google Picker, otherwise Google
            # Picker refuses to launch in an iframe.
            "origin": self._request.lti_params.get(
                "custom_canvas_api_domain", application_instance.lms_url
            ),
        }

    @classmethod
    def factory(cls, _context, request):
        return GoogleFiles(
            request=request,
            client_id=request.registry.settings["google_client_id"],
            developer_key=request.registry.settings["google_developer_key"],
        )
