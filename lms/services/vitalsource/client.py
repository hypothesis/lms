import re
from typing import Optional, TypedDict, Union

import requests
import xmltodict

from lms.models import LTIParams
from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.vitalsource._schemas import BookInfoSchema, BookTOCSchema

#: A regex for parsing the BOOK_ID and CFI parts out of one of our custom
#: vitalsource://book/bookID/BOOK_ID/cfi/CFI URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"vitalsource:\/\/book\/bookID\/(?P<book_id>[^\/]*)\/cfi\/(?P<cfi>.*)"
)


class BookLocation(TypedDict):
    """Book ID and chapter extracted from a "vitalsource://..." document URL."""

    book_id: str
    cfi: str


class VitalSourceUserNotFoundError(Exception):
    """LTI user could not be matched to a VitalSource user."""

    error_code = "vitalsource_user_not_found"


class VitalSourceLicenseError(Exception):
    """User does not have a license for the book."""

    error_code = "vitalsource_no_book_license"


class VitalSourceService:
    """
    Service for querying the VitalSource API.

    See https://developer.vitalsource.com/hc/en-us for API reference.
    """

    def __init__(
        self,
        http_service: HTTPService,
        metadata_api_key: str,
        user_api_key: str,
        lti_user_field: str,
    ):
        """
        Return a new VitalSourceService.

        :param metadata_api_key: API key for book metadata requests. This key
          is not specific to the LTI user's institution.
        :param user_api_key: API key for requests to access user-specific
          information. This will be a key that is specific to the LTI user's
          institution.
        :param lti_user_field: The field from the LTI launch request which
          is used to identify the current user
        :raises ValueError: If credentials are invalid
        """
        self._http_service = http_service
        self._metadata_api_key = metadata_api_key
        self._user_api_key = user_api_key
        self._lti_user_field = lti_user_field

    def book_info(self, book_id: str):
        try:
            response = self._request(self._metadata_api_key, f"v4/products/{book_id}")
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        return BookInfoSchema(response).parse()

    def book_toc(self, book_id: str):
        try:
            response = self._request(
                self._metadata_api_key, f"v4/products/{book_id}/toc"
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        schema = BookTOCSchema(response)
        schema.context["book_id"] = book_id
        return schema.parse()

    def get_user_reference(self, lti_params: LTIParams) -> str:
        """
        Extract the VitalSource user reference from the LTI launch parameters.

        The user reference is a string which can subsequently be passed to
        `get_user_access_token` to make VitalSource API calls on behalf of
        the current LTI user. Which field of the LTI launch parameters is
        used as a reference depends on how VitalSource is configured at an
        institution.
        """
        return lti_params[self._lti_user_field]

    def get_user_access_token(self, user_reference: str) -> str:
        """
        Get an access token for the current LTI user.

        This generates an access token that can be used with user-specific
        queries such as `user_has_book_license` and `book_reader_url`.

        One of the LTI launch request properties from `lti_params` will be
        passed to VitalSource to identify the current user. Which one depends
        on the LMS installation.

        :param user_reference: String identifying the current user. This must
          be extracted from the LTI launch parameters during the initial
          assignment launch, using `get_user_reference`.
        """

        data = {
            "credentials": {
                "credential": {"@reference": user_reference},
            }
        }
        result = self._xml_request(self._user_api_key, "v3/credentials.xml", data=data)

        credentials = result["credentials"].get("credential")
        if not credentials:
            raise VitalSourceUserNotFoundError()

        if isinstance(credentials, list):
            credentials = credentials[0]
        return credentials["@access-token"]

    def user_has_book_license(self, access_token: str, book_id: str) -> bool:
        """
        Check whether a user has a license to access a book.

        :param access_token: Token previously obtained via `get_user_access_token`
        """
        result = self._xml_request(
            self._user_api_key,
            "v3/licenses.xml",
            params={"sku": book_id},
            access_token=access_token,
        )

        # The result is a list of active licenses that match the given book ID/SKU.
        # Check that we have at least one.
        return result["licenses"] and "license" in result["licenses"]

    def user_opted_out(self, course_id, book_id: str) -> bool:
        response = self._request(
            api_key=self._user_api_key,
            endpoint=f"https://launch.vitalsource.com/api/v4/courses/{course_id}/opt_outs",
            json=True,
        )
        print(response)
        return False

    def get_courses(self):
        response = self._request(
            api_key=self._user_api_key,
            endpoint=f"https://launch.vitalsource.com/api/v4/courses",
            json=True,
        )
        print(response)
        return False

    def get_launch_url(self, book_id: str, cfi: str, user_reference: str) -> str:
        """
        Return a temporary URL to load the VitalSource book viewer.

        The returned URL will automatically log the user into the VitalSource
        book reader with the account that corresponds to the current LMS user.

        :param book_id: The book to open
        :param cfi: The location to navigate to within the book
        :param user_reference: User identifier extracted from LTI launch
          parameters using `get_user_reference`.
        """
        access_token = self.get_user_access_token(user_reference)
        if not self.user_has_book_license(access_token, book_id):
            raise VitalSourceLicenseError()

        # TBD: Do we want to support a mode where SSO is not used? In this case
        # we should just return this URL directly.
        destination = f"https://hypothesis.vitalsource.com/books/{book_id}/cfi/{cfi}"

        data = {"redirect": {"destination": destination}}
        result = self._xml_request(
            self._user_api_key, "v3/redirects.xml", data=data, access_token=access_token
        )
        return result["redirect"]["@auto-signin"]

    def _xml_request(
        self,
        api_key: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        access_token: Optional[str] = None,
    ) -> dict:
        """
        Make a request to a VitalSource endpoint that accepts/returns XML.

        The VitalSource API endpoints prefixed with "v3/" use XML. The
        endpoints prefixed with "v4/" use JSON instead.
        """

        xml_data = xmltodict.unparse(data) if data else None
        response = self._request(api_key, endpoint, params, xml_data, access_token)
        return xmltodict.parse(response.text)

    def _request(
        self,
        api_key: str,
        endpoint: str,
        params: Optional[dict] = None,
        data: Union[str, Optional[dict]] = None,
        access_token: Optional[str] = None,
        json=False,
    ) -> requests.Response:
        """
        Make a request to the VitalSource API.

        :param params: Query parameters
        :param data: Request body to send. This can either be a dict which will
          be sent as JSON, or a string of XML for v3 APIs.
        :param access_token: Access token to identify and authenticate the
          current user. Only needed for user-specific endpoints.
        """

        method = "POST" if data else "GET"
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"https://api.vitalsource.com/{endpoint}"

        headers = {"X-VitalSource-API-Key": api_key}
        if json:
            headers["accept"] = "application/json"
            headers["content-type"] = "application/json"
        if access_token:
            headers["X-VitalSource-Access-Token"] = access_token

        response = self._http_service.request(
            method=method, url=url, params=params, headers=headers, data=data
        )
        response.raise_for_status()

        return response

    @staticmethod
    def parse_document_url(document_url: str) -> BookLocation:
        """Extract the book ID and location from a `vitalsource://` URL."""
        return DOCUMENT_URL_REGEX.search(document_url).groupdict()

    @staticmethod
    def generate_document_url(book_id, cfi):
        return f"vitalsource://book/bookID/{book_id}/cfi/{cfi}"


def factory(_context, request):
    ai_settings = (
        request.find_service(name="application_instance").get_current().settings
    )
    return VitalSourceService(
        http_service=request.find_service(name="http"),
        metadata_api_key=request.registry.settings["vitalsource_api_key"],
        user_api_key=ai_settings.get("vitalsource", "api_key"),
        lti_user_field=ai_settings.get("vitalsource", "lti_user_field"),
    )
