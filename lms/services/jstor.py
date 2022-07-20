from datetime import timedelta
from html.parser import HTMLParser
from urllib.parse import quote

import requests
from marshmallow import fields

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.jwt import JWTService
from lms.validation._base import RequestsResponseSchema
from lms.views.helpers import via_url


class JSTORMetadataSchema(RequestsResponseSchema):
    """
    Response schema for `/metadata/{doi}` endpoint in the JSTOR API.

    See https://labs.jstor.org/api/anno/docs
    """

    title = fields.Str()
    subtitle = fields.Str()

    # List of titles of works that this item is a review of.
    reviewed_works = fields.List(fields.Str())


class JSTORService:
    """An interface for dealing with JSTOR documents."""

    DEFAULT_DOI_PREFIX = "10.2307"
    """Used when no DOI prefix can be found."""

    # pylint: disable=too-many-arguments
    def __init__(self, api_url, secret, enabled, site_code, http_service: HTTPService):
        """
        Initialise the JSTOR service.

        :param api_url: JSTOR API url
        :param secret: Secret for authenticating with JSTOR
        :param enabled: Whether JSTOR is enabled on this instance
        :param site_code: The site code to use to identify the organization
        :param http_service: HTTPService instance
        """
        self._api_url = api_url
        self._secret = secret
        self._enabled = enabled
        self._site_code = site_code

        self._http = http_service

    @property
    def enabled(self) -> bool:
        """Get whether this instance is configured for JSTOR."""

        return bool(self._enabled and self._api_url and self._site_code)

    def via_url(self, request, document_url):
        """
        Get a VIA url for a document.

        :param request: Pyramid request
        :param document_url: The URL to annotate
        :return: A URL for Via configured to launch the requested document
        :raises ExternalRequestError: If we get a value which doesn't look like
            a public URL from JSTOR
        """

        # Get a signed S3 URL for the given JSTOR URL.
        s3_url = self._api_request(
            "/pdf-url/{doi}", doi=document_url.replace("jstor://", "")
        ).text

        if not s3_url.startswith("https://"):
            raise ExternalRequestError(
                f"Expected to get an S3 URL but got: '{s3_url}' instead"
            )

        return via_url(
            request,
            document_url=s3_url,
            content_type="pdf",
            # Show content partner banner in client for JSTOR.
            options={"via.client.contentPartner": "jstor"},
        )

    def metadata(self, article_id: str):
        """
        Fetch metadata about a JSTOR article.

        :param article_id: A JSTOR article ID or DOI
        """

        response = self._api_request("/metadata/{doi}", doi=article_id)
        metadata = JSTORMetadataSchema(response).parse()

        return {"title": self._get_title_from_metadata(metadata)}

    def thumbnail(self, article_id: str):
        """
        Fetch a thumbnail image for an article.

        Returns a `data:` URI with base64-encoded data which can be used as the
        source for an `<img>` element.

        :param article_id: A JSTOR article ID or DOI
        :raise ExternalRequestError: If the response doesn't look like a valid
            `data:` URI
        """

        data_uri = self._api_request(
            "/thumbnail/{doi}",
            doi=article_id,
            params={
                # `offset` specifies the page number. The default value of 0
                # returns the thumbnail of the last page. Setting it to 1
                # returns the first page.
                "offset": 1,
                # The frontend displays the image with a width of ~140px,
                # so 280px has enough resolution for a 2x device pixel ratio.
                # The height will be adjusted to maintain the aspect ratio.
                "width": 280,
            },
        ).text

        if not data_uri.startswith("data:"):
            raise ExternalRequestError(
                f"Expected to get data URI but got '{data_uri}' instead"
            )

        return data_uri

    def _api_request(self, path_template, doi, params=None) -> requests.Response:
        """
        Call the JSTOR API with a URL based on an article id.

        See the JSTOR API's `/docs` endpoint for details.
        """

        if "/" not in doi:
            doi = f"{self.DEFAULT_DOI_PREFIX}/{doi}"

        url = self._api_url + path_template.format(doi=quote(doi, safe="/"))

        token = JWTService.encode_with_secret(
            {"site_code": self._site_code},
            secret=self._secret,
            lifetime=timedelta(hours=1),
        )
        return self._http.get(
            url=url, headers={"Authorization": f"Bearer {token}"}, params=params
        )

    @classmethod
    def _get_title_from_metadata(cls, metadata: dict) -> str:
        # Reviews of other works may not have a title of their own, but we can
        # generate one from the reviewed work's metadata.
        if reviewed_works := metadata.get("reviewed_works"):
            title = f"Review: {reviewed_works[0]}"

        # Journal articles, book chapters and research reports have a title
        # field with a single entry.
        elif title := metadata.get("title"):

            # Some articles have a subtitle which needs to be appended for the
            # title to make sense.
            if subtitle := metadata.get("subtitle"):
                # Some titles include a trailing ':' delimiter, some do not.
                title = f"{title.rstrip(':')}: {subtitle}"

        else:
            title = "[Unknown title]"

        # Some titles contain HTML formatting tags, new lines or unwanted
        # extra spaces. Strip these to simplify downstream processing.
        return cls._strip_html_tags(title)

    @staticmethod
    def _strip_html_tags(html: str) -> str:
        """Get plain text from a string which may contain HTML tags."""

        # Extract text nodes using HTMLParser. We rely on it being tolerant of
        # invalid markup.
        chunks = []
        parser = HTMLParser()
        parser.handle_data = chunks.append
        parser.feed(html)
        parser.close()

        # Strip leading/trailing whitespace and duplicate spaces
        return " ".join("".join(chunks).split())


def factory(_context, request):
    ai_settings = (
        request.find_service(name="application_instance").get_current().settings
    )

    app_settings = request.registry.settings

    return JSTORService(
        api_url=app_settings.get("jstor_api_url"),
        secret=app_settings.get("jstor_api_secret"),
        enabled=ai_settings.get("jstor", "enabled"),
        site_code=ai_settings.get("jstor", "site_code"),
        http_service=request.find_service(name="http"),
    )
