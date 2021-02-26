"""Via-related view helpers."""
from h_vialib import ViaClient

__all__ = ["via_url"]


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
    return ViaClient(
        service_url=request.registry.settings["via_url"],
        host_url=request.host_url,
        secret=request.registry.settings["via_secret"],
    ).url_for(document_url, content_type, blocked_for="lms")
