from lms.content_source.content_source import ContentSource


class MicrosoftOnedrive(ContentSource):
    url_scheme = None
    config_key = "microsoftOneDrive"

    def __init__(self, client_id, redirect_uri):
        self._client_id = client_id
        self._redirect_uri = redirect_uri

    def is_enabled(self, application_instance):
        return application_instance.settings.get(
            "microsoft_onedrive", "files_enabled", default=True
        )

    def get_picker_config(self, application_instance):
        return {
            "clientId": self._client_id,
            "redirectURI": self._redirect_uri,
        }

    @classmethod
    def factory(cls, _context, request):
        return MicrosoftOnedrive(
            client_id=request.registry.settings["onedrive_client_id"],
            redirect_uri=request.route_url("onedrive.filepicker.redirect_uri"),
        )
