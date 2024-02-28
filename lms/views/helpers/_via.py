"""Via-related view helpers."""

from urllib.parse import urlencode, urlparse, urlunparse

from h_vialib import ViaClient

__all__ = ["via_url"]


def _common_via_params(request) -> dict:
    return {
        "via.client.requestConfigFromFrame.origin": request.host_url,
        "via.client.requestConfigFromFrame.ancestorLevel": "2",
    }


def via_url(  # pylint:disable=too-many-arguments
    request, document_url, content_type=None, options=None, headers=None, query=None
):
    """
    Return the Via URL for annotating the given ``document_url``.

    The location of Via is controlled with the VIA_URL environment variable.

    Return the URL to be used as the ``src`` attribute of the Via iframe in
    order to annotate the given ``document_url``.

    :param request: Request object
    :param document_url: Document URL to present in Via
    :param content_type: Either "pdf" or "html" if known, None if not
    :param options: Any extra options for the url
    :param headers: Headers for the request to `document_url`
    :param query: Query parameters for the request to `document_url`. Encrypted on transit.
    :return: A URL string
    """
    if not options:
        options = {}

    options.update(_common_via_params(request))

    return ViaClient(
        service_url=request.registry.settings["via_url"],
        secret=request.registry.settings["via_secret"],
    ).url_for(
        document_url,
        content_type,
        blocked_for="lms",
        options=options,
        headers=headers,
        query=query,
    )


def via_video_url(
    request, canonical_url: str, download_url: str, transcript_url: str
) -> str:
    """
    Return the URL for annotating a video transcript through Via.

    :param canonical_url: URL to save with annotations
    :param download_url:
        URL that can be used with a `<video>` element to display the video.
    :param transcript_url:
        URL of the video's transcript, in SRT or WebVTT formats.
    """
    via_service_url = urlparse(request.registry.settings["via_url"])
    via_url = urlunparse(
        (
            via_service_url.scheme,
            via_service_url.netloc,
            "video",
            "",
            urlencode(
                {
                    **_common_via_params(request),
                    "url": canonical_url,
                    "media_url": download_url,
                    "transcript": transcript_url,
                    # TODO - Add `title` field
                }
            ),
            "",
        )
    )
    return via_url
