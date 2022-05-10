from datetime import timedelta

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
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
        """

        return via_url(
            request,
            document_url=self._get_public_url(document_url),
            content_type="pdf",
            # Show content partner banner in client for JSTOR.
            options={"via.client.contentPartner": "jstor"},
        )

    def _get_public_url(self, url):
        """
        Get a signed S3 URL for the given JSTOR URL.

        :param url: The URL to stream
        :return: A public URL
        :raises ExternalRequestError: If we get bad data back from the service
        """

        doi = url.replace("jstor://", "")
        if "/" not in doi:
            doi = f"{self.DEFAULT_DOI_PREFIX}/{doi}"

        token = JWTService.encode_with_secret(
            {"site_code": self._site_code},
            secret=self._secret,
            lifetime=timedelta(hours=1),
        )

        s3_url = self._http.request(
            method="GET",
            url=f"{self._api_url}/pdf-url/{doi}",
            headers={"Authorization": f"Bearer {token}"},
        ).text

        if not s3_url.startswith("https://"):
            raise ExternalRequestError(
                f"Expected to get an S3 URL but got: '{s3_url}' instead"
            )

        return s3_url


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
