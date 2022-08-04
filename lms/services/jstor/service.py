from datetime import timedelta
from urllib.parse import quote

import requests

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.jstor._article_metadata import ArticleMetadata
from lms.services.jwt import JWTService
from lms.views.helpers import via_url


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
            "/pdf/{doi}", doi=document_url.replace("jstor://", "")
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

    def get_article_metadata(self, article_id: str):
        """
        Fetch metadata about a JSTOR article.

        :param article_id: A JSTOR article ID or DOI
        """

        response = self._api_request("/metadata/{doi}", doi=article_id)

        return ArticleMetadata.from_response(response).as_dict()

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
