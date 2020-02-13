"""Via-related view helpers."""
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

__all__ = ["via_url"]


def via_url(request, document_url):
    """
    Return the Via URL for annotating the given ``document_url``.

    Return the URL to be used as the ``src`` attribute of the Via iframe in
    order to annotate the given ``document_url``.

    :param request:
    :param document_url:
    :return:
    """

    options = {
        "via.open_sidebar": "1",
        "via.request_config_from_frame": request.host_url,
    }

    if request.feature("use_via3_url"):
        return _via3_url(
            via_service_url=request.registry.settings["via3_url"],
            document_url=document_url,
            options=options
        )

    return _legacy_via_url(
        via_service_url=request.registry.settings["via_url"],
        document_url=document_url,
        options=options
    )


def _via3_url(via_service_url, document_url, options):
    options['url'] = document_url

    url = urlparse(via_service_url)._replace(query=urlencode(options))
    return url.geturl()


def _legacy_via_url(via_service_url, document_url, options):
    """
    For legacy via example::

      https://via.hypothes.is/https://example.com/document?via.open_sidebar=1&via...

    The ``https://via.hypothes.is`` part depends on the value of the VIA_URL
    environment variable.

    The ``https://example.com/document`` part is the ``document_url`` argument
    passed to this function.

    The ``?via.*=foo&via.*=bar`` query parameters enable non-default Via and
    client features that're required. Any existing non-Via query parameters on
    the document URL are preserved in their original order.

    :arg str document_url: the URL of the document to be annotated
    :return: the Via URL for this assignment
    :rtype: str

    """
    parts = urlparse(document_url)

    query_string_as_list = parse_qsl(parts.query)
    query_string_as_list = [
        t for t in query_string_as_list if not t[0].startswith("via.")
    ]
    for key, value in options.items():
        query_string_as_list.append((key, value))

    query_string = urlencode(query_string_as_list)

    return via_service_url + urlunparse(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            parts.params,
            query_string,
            parts.fragment,
        )
    )
