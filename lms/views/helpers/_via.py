"""Via-related view helpers."""
from urllib.parse import parse_qsl, urlencode, urlparse

__all__ = ["via_url"]


def via_url(request, document_url):
    """
    Return the Via URL for annotating the given ``document_url``.

    The location of Via is controlled with the VIA_URL environment variable.

    Return the URL to be used as the ``src`` attribute of the Via iframe in
    order to annotate the given ``document_url``.

    :param request: Request object
    :param document_url: Document URL to present in Via
    :return: A URL string
    """

    # Default via parameters
    options = {
        "via.open_sidebar": "1",
        "via.request_config_from_frame": request.host_url,
        "via.config_frame_ancestor_level": "2",
    }

    if request.feature("use_legacy_via"):
        return _legacy_via_url(
            request.registry.settings["legacy_via_url"], document_url, options
        )

    options["url"] = document_url
    via_service_url = urlparse(request.registry.settings["via_url"])

    return via_service_url._replace(path="/route", query=urlencode(options)).geturl()


def _legacy_via_url(via_service_url, document_url, options):
    parsed_url = urlparse(document_url)

    params = [kv for kv in parse_qsl(parsed_url.query) if not kv[0].startswith("via.")]
    params.extend(options.items())

    return via_service_url + parsed_url._replace(query=urlencode(params)).geturl()
