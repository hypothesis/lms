from lms.views.helpers import via_url


class JSTORService:
    def __init__(self, settings):
        self._settings = settings

    @property
    def enabled(self):
        return self._settings.get("enabled", False)

    @staticmethod
    def via_url(request, document_url):
        return via_url(
            request,
            document_url,
            content_type="pdf",
            options={"jstor.ip": request.registry.settings["jstor_ip"]},
        )


def factory(_context, request):
    # application_instance.settings is an ApplicationSettings which overwrites `get`.
    # Convert to a dict to be able to access ["jstor"] securely
    settings = dict(
        request.find_service(name="application_instance").get_current().settings
    )
    return JSTORService(settings=settings.get("jstor", {}))
