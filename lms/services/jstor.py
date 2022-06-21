from datetime import timedelta
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import quote

import requests
from marshmallow import EXCLUDE, Schema, fields

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.jwt import JWTService
from lms.validation._base import RequestsResponseSchema
from lms.views.helpers import via_url


class JSTORMetadataSchema(RequestsResponseSchema):
    """Response schema for `/metadata/{doi}` endpoint in the JSTOR API."""

    # Title fields for "regular" articles.
    title = fields.List(fields.Str())
    subtitle = fields.List(fields.Str())

    # Title fields for collections (eg. books).
    # These may be present but set to `null` for other types of article.
    tb = fields.Str(allow_none=True)
    tbsub = fields.Str(allow_none=True)

    # Fields for articles which are reviews of other works.

    class ReviewedWorks(Schema):
        title = fields.Str()

    reviewed_works = fields.List(fields.Nested(ReviewedWorks, unknown=EXCLUDE))


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
        """

        return via_url(
            request,
            document_url=self._get_public_url(document_url),
            content_type="pdf",
            # Show content partner banner in client for JSTOR.
            options={"via.client.contentPartner": "jstor"},
        )

    def metadata(self, article_id: str):
        """
        Fetch metadata about a JSTOR article.

        :param article_id: A JSTOR article ID or DOI
        """
        doi = self._doi_from_article_id(article_id)
        response = self._api_request(_format_uri("/metadata/{}", doi))
        metadata = JSTORMetadataSchema(response).parse()

        title = self._get_title_from_metadata(metadata)

        return {"title": title}

    def thumbnail(self, article_id: str):
        """
        Fetch a thumbnail image for an article.

        Returns a `data:` URI with base64-encoded data which can be used as the
        source for an `<img>` element.

        :param article_id: A JSTOR article ID or DOI
        :raise ExternalRequestError: If the response doesn't look like a valid `data:` URI
        """
        doi = self._doi_from_article_id(article_id)
        params = {
            # `offset` specifies the page number. The default value of 0 returns
            # the thumbnail of the last page. Setting it to 1 returns the first
            # page.
            "offset": 1,
            # The frontend currently displays the image with a width of ~140px,
            # so 280px has enough resolution for a 2x device pixel ratio.
            # The height will be adjusted to maintain the aspect ratio.
            "width": 280,
        }
        data_uri = self._api_request(
            _format_uri("/thumbnail/{}", doi), params=params
        ).text

        if not data_uri.startswith("data:"):
            raise ExternalRequestError(
                f"Expected to get data URI but got '{data_uri}' instead"
            )

        return data_uri

    def _get_public_url(self, url):
        """
        Get a signed S3 URL for the given JSTOR URL.

        :param url: The URL to stream
        :return: A public URL
        :raises ExternalRequestError: If we get bad data back from the service
        """

        article_id = url.replace("jstor://", "")
        doi = self._doi_from_article_id(article_id)
        s3_url = self._api_request(_format_uri("/pdf-url/{}", doi)).text

        if not s3_url.startswith("https://"):
            raise ExternalRequestError(
                f"Expected to get an S3 URL but got: '{s3_url}' instead"
            )

        return s3_url

    def _api_request(
        self, endpoint: str, params: Optional[dict] = None
    ) -> requests.Response:
        """
        Make an authenticated request to the JSTOR API.

        See the JSTOR API's `/docs` endpoint for details.
        """
        token = JWTService.encode_with_secret(
            {"site_code": self._site_code},
            secret=self._secret,
            lifetime=timedelta(hours=1),
        )
        url = self._api_url + endpoint
        return self._http.get(
            url=url, headers={"Authorization": f"Bearer {token}"}, params=params
        )

    def _doi_from_article_id(self, article_id):
        if "/" not in article_id:
            return f"{self.DEFAULT_DOI_PREFIX}/{article_id}"
        return article_id

    @classmethod
    def _get_title_from_metadata(cls, metadata: dict) -> Optional[str]:
        subtitle = None

        # "Regular" articles have a title field with a single entry.
        if titles := metadata.get("title"):
            title = titles[0]

            # Some articles have a subtitle which needs to be appended for the
            # title to make sense.
            if subtitles := metadata.get("subtitle"):
                subtitle = subtitles[0]

        # Collections (eg. books) have their title in separate field
        elif collection_title := metadata.get("tb"):
            title = collection_title
            subtitle = metadata.get("tbsub")

        # Reviews of other works may not have a title of their own, but we can
        # generate one from the reviewed work's metadata.
        elif reviewed_works := metadata.get("reviewed_works"):
            title = f'Review: {reviewed_works[0]["title"]}'
        else:
            return None

        if subtitle:
            title = f"{title} {subtitle}"

        # Some titles contain HTML formatting tags, new lines or unwanted
        # extra spaces. Strip these to simplify downstream processing.
        return _normalize_whitespace(_strip_html_tags(title))


def _format_uri(template: str, *params: str):
    """
    Format a URI string.

    This is like `template.format(*params)` except that the params are
    percent-encoded.
    """
    encoded = [quote(param, safe="/") for param in params]
    return template.format(*encoded)


def _strip_html_tags(html: str) -> str:
    """Extract plain text from a string which may contain HTML formatting tags."""

    # Extract text nodes using HTMLParser. We rely on it being tolerant of
    # invalid markup.
    chunks = []
    parser = HTMLParser()
    parser.handle_data = chunks.append
    parser.feed(html)
    parser.close()

    return "".join(chunks)


def _normalize_whitespace(val: str) -> str:
    """Convert all whitespace to single spaces and remove leading/trailing spaces."""
    return " ".join(val.split())


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
