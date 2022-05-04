from lms.views.helpers import via_url


class JSTORService:
    def __init__(self, enabled, site_code):
        """
        Initialise the JSTOR service.

        :param enabled: Whether JSTOR is enabled on this instance
        :param site_code: The site code to use to identify the organization
        """
        self._enabled = enabled
        self._site_code = site_code

    @property
    def enabled(self) -> bool:
        """Get whether this instance is configured for JSTOR."""

        return bool(self._enabled and self._site_code)

    def via_url(self, request, document_url):
        """
        Get a VIA url for a document.

        :param request: Pyramid request
        :param document_url: The URL to annotate
        :return: A URL for Via configured to launch the requested document
        """

        return via_url(
            request,
            document_url,
            content_type="pdf",
            options={"via.jstor.site_code": self._site_code},
        )


def factory(_context, request):
    settings = request.find_service(name="application_instance").get_current().settings

    return JSTORService(
        enabled=settings.get("jstor", "enabled"),
        site_code=settings.get("jstor", "site_code"),
    )
