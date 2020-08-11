"""Via-related view helpers."""
import re
from urllib.parse import parse_qsl, urlencode, urlparse

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

    @property
    def is_html(self):
        return self._content_type == "html"


class _ViaClient:
    """A small wrapper to make calling Via easier."""

    def __init__(
        # pylint: disable=too-many-arguments
        self,
        service_url,
        legacy_service_url,
        host_url,
        legacy_mode=False,
        via_rewriter_mode=False,
    ):
        self.service_url = urlparse(service_url)
        self.legacy_service_url = legacy_service_url

        # Default via parameters
        self.options = {
            "via.client.openSidebar": "1",
            "via.client.requestConfigFromFrame.origin": host_url,
            "via.client.requestConfigFromFrame.ancestorLevel": "2",
            "via.external_link_mode": "new-tab",
        }

        self.legacy_mode = legacy_mode
        self.via_rewriter_mode = via_rewriter_mode

    def url_for(self, doc):
        if self.legacy_mode:
            return self._legacy_via_url(doc.url)

        if doc.is_html:
            if self.via_rewriter_mode:
                return self._pywb_style_url(
                    self.service_url._replace(path="/html/v/").geturl(), doc.url
                )

            return self._legacy_via_url(doc.url)

        if doc.is_pdf:
            return self._url_for("/pdf", doc.url)

        if self.via_rewriter_mode:
            self.options["via.rewrite"] = "1"

        return self._url_for("/route", doc.url)

    def _url_for(self, path, doc_url):
        options = {"url": doc_url}
        options.update(self.options)

        return self.service_url._replace(path=path, query=urlencode(options)).geturl()

    def _legacy_via_url(self, doc_url):
        return self._pywb_style_url(self.legacy_service_url, doc_url)

    def _pywb_style_url(self, base_url, doc_url):
        parsed_url = urlparse(doc_url)

        params = [
            kv for kv in parse_qsl(parsed_url.query) if not kv[0].startswith("via.")
        ]
        params.extend(self.options.items())

        return base_url + parsed_url._replace(query=urlencode(params)).geturl()


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
        service_url=request.registry.settings["via_url"],
        legacy_service_url=request.registry.settings["legacy_via_url"],
        host_url=request.host_url,
        legacy_mode=request.feature("use_legacy_via"),
        via_rewriter_mode=request.feature("use_via_rewriter"),
    ).url_for(doc)
