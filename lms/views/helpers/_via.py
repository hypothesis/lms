"""Via-related view helpers."""
from urllib import parse

__all__ = ["via_url"]


def via_url(request, document_url):
    """
    Return the Via URL for annotating the given ``document_url``.

    Return the URL to be used as the ``src`` attribute of the Via iframe in
    order to annotate the given ``document_url``. For example::

      https://via.hypothes.is/https://example.com/document?via.open_sidebar=1&via...

    The ``https://via.hypothes.is`` part depends on the value of the VIA_URL
    environment variable.

    The ``https://example.com/document`` part is the ``document_url`` argument
    passed to this function.

    The ``?via.*=foo&via.*=bar`` query parameters enable non-default Via and
    client features that're required. Any existing non-Via query parameters on
    the document URL are preserved in their original order.

    :arg pyramid.request.Request request: the Pyramid request
    :arg str document_url: the URL of the document to be annotated
    :return: the Via URL for this assignment
    :rtype: str

    """
    parts = parse.urlparse(document_url)

    query_string_as_list = parse.parse_qsl(parts.query)
    query_string_as_list = [
        t for t in query_string_as_list if not t[0].startswith("via.")
    ]
    query_string_as_list.append(("via.open_sidebar", "1"))
    query_string_as_list.append(("via.request_config_from_frame", request.host_url))

    if request.feature("pdfjs2"):
        query_string_as_list.append(("via.features", "pdfjs2"))

    query_string = parse.urlencode(query_string_as_list)

    via_service_url = request.registry.settings["via_url"]
    if request.feature("use_via2_service"):
        via_service_url = request.registry.settings["via2_url"]

    return via_service_url + parse.urlunparse(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            parts.params,
            query_string,
            parts.fragment,
        )
    )
