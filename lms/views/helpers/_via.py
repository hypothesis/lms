"""Via-related view helpers."""
import re
from urllib.parse import urlencode, urlparse

__all__ = ["via_url"]


class _ViaDoc:
    """A doc we want to proxy with content type."""

    GOOGLE_DRIVE_REGEX = re.compile(
        r"^https://drive.google.com/uc\?id=(.*)&export=download$", re.IGNORECASE
    )

    def __init__(self, url, content_type=None):
        self.url = url

        if content_type is None and self.GOOGLE_DRIVE_REGEX.match(url):
            content_type = "pdf"

        self._content_type = content_type

    @property
    def is_pdf(self):
        return self._content_type == "pdf"


class _ViaClient:
    """A small wrapper to make calling Via easier."""

    def __init__(self, service_url, host_url):
        self.service_url = urlparse(service_url)

        # Default via parameters
        self.options = {
            "via.client.openSidebar": "1",
            "via.client.requestConfigFromFrame.origin": host_url,
            "via.client.requestConfigFromFrame.ancestorLevel": "2",
            "via.external_link_mode": "new-tab",
        }

    def url_for(self, doc):
        # Optimisation to skip routing for documents we know are PDFs
        path = "/pdf" if doc.is_pdf else "/route"

        options = {"url": doc.url}
        options.update(self.options)

        return self.service_url._replace(path=path, query=urlencode(options)).geturl()


def via_url(request, document_url, content_type=None):
    """
    Return the Via URL for annotating the given ``document_url``.

    The location of Via is controlled with the VIA_URL environment variable.

    Return the URL to be used as the ``src`` attribute of the Via iframe in
    order to annotate the given ``document_url``.

    :param request: Request object
    :param document_url: Document URL to present in Via
    :param content_type: Either "pdf" or "html" if known, None if not
    :return: A URL string
    """

    doc = _ViaDoc(document_url, content_type)

    return _ViaClient(
        service_url=request.registry.settings["via_url"], host_url=request.host_url
    ).url_for(doc)
