import re
from typing import Dict, Tuple

import oauthlib
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_BODY

from lms.models.lti_user import LTIUser
from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource._schemas import BookInfoSchema, BookTOCSchema

#: A regex for parsing the BOOK_ID and CFI parts out of one of our custom
#: vitalsource://book/bookID/BOOK_ID/cfi/CFI URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"vitalsource:\/\/book\/bookID\/(?P<book_id>[^\/]*)\/cfi\/(?P<cfi>.*)"
)


class VitalSourceService:
    def __init__(
        self,
        http_service,
        lti_launch_key: str,
        lti_launch_secret: str,
        api_key: str,
    ):
        """
        Return a new VitalSourceService.

        :param api_key: Key for VitalSource API
        :param lti_launch_key: OAuth consumer key for LTI launches. If omitted,
            a direct/non-LTI launch is used.
        :param lti_launch_secret: OAuth consumer secret for LTI launches. Only
            required if `lti_launch_key` is set.
        :raises ValueError: If credentials are invalid
        """
        if not all([lti_launch_key, lti_launch_secret, api_key]):
            raise ValueError("VitalSource credentials are missing")

        self._http_service = http_service
        self._api_key = api_key
        self._lti_launch_key = lti_launch_key
        self._lti_launch_secret = lti_launch_secret

    def get(self, endpoint):
        url = f"https://api.vitalsource.com/v4/{endpoint}"

        return self._http_service.get(
            url, headers={"X-VitalSource-API-Key": self._api_key}
        )

    def book_info(self, book_id: str):
        try:
            response = self.get(f"products/{book_id}")
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        return BookInfoSchema(response).parse()

    def book_toc(self, book_id: str):
        try:
            response = self.get(f"products/{book_id}/toc")
        except ExternalRequestError as err:
            if err.status_code == 404:
                err.message = f"Book {book_id} not found"

            raise

        schema = BookTOCSchema(response)
        schema.context["book_id"] = book_id
        return schema.parse()

    @staticmethod
    def parse_document_url(document_url):
        return DOCUMENT_URL_REGEX.search(document_url).groupdict()

    @staticmethod
    def generate_document_url(book_id, cfi):
        return f"vitalsource://book/bookID/{book_id}/cfi/{cfi}"

    def get_launch_url(self, document_url: str) -> str:
        """
        Return a URL to load the VitalSource book viewer at a particular book and location.

        That URL can be used to load VitalSource content in an iframe like we do with other types of content.

        Note that this method is an alternative to `get_launch_params` below.

        :param document_url: `vitalsource://` type URL identifying the document
        """
        url_params = self.parse_document_url(document_url)
        return f"https://hypothesis.vitalsource.com/books/{url_params['book_id']}/cfi/{url_params['cfi']}"

    def get_launch_params(
        self, document_url, lti_user: LTIUser
    ) -> Tuple[str, Dict[str, str]]:
        """
        Return the parameters needed to launch the VitalSource book viewer.

        This method is deprecated in favour of `get_launch_url` above.

        The VitalSource book viewer is launched using an LTI launch. This involves
        posting an HTML form containing the book ID and location along with metadata
        about the current user and an OAuth 1.0 signature.

        See https://developer.vitalsource.com/hc/en-us/articles/215612237-POST-LTI-Create-a-Bookshelf-Launch

        :param document_url: `vitalsource://` type URL identifying the document
        :param lti_user: Current LTI user information
        :return: (launch_url, form_params) tuple.
        """
        url_params = self.parse_document_url(document_url)
        book_id = url_params["book_id"]
        cfi = url_params["cfi"]

        launch_url = f"https://bc.vitalsource.com/books/{book_id}"
        book_location = "/cfi" + cfi

        launch_params = self._launch_params(
            user_id=lti_user.user_id,
            roles=lti_user.roles,
            # Set a dummy `context_id`. This needs to be replaced with the real
            # course in future.
            context_id="testcourse",
            location=book_location,
        )
        self._sign_form_params(launch_url, launch_params)

        return (launch_url, launch_params)

    def _sign_form_params(self, url, params):
        client = oauthlib.oauth1.Client(
            self._lti_launch_key,
            self._lti_launch_secret,
            signature_method=SIGNATURE_HMAC_SHA1,
            signature_type=SIGNATURE_TYPE_BODY,
        )
        params.update(client.get_oauth_params(oauthlib.common.Request(url, "POST")))
        oauth_request = oauthlib.common.Request(url, "POST", body=params)
        params["oauth_signature"] = client.get_oauth_signature(oauth_request)
        return params

    @staticmethod
    def _launch_params(user_id, roles, context_id, location):
        # See https://developer.vitalsource.com/hc/en-us/articles/206156238-General-LTI-Usage
        params = {
            # Standard LTI launch parameters
            "lti_version": "LTI-1p0",
            "lti_message_type": "basic-lti-launch-request",
            # User data. These should be proxied from the LTI launch.
            "user_id": user_id,
            "roles": roles,
            "context_id": context_id,
            # Book presentation and location options
            "launch_presentation_document_target": "window",
            "custom_book_location": location,
        }

        return params


def factory(_context, request):
    return VitalSourceService(
        request.find_service(name="http"),
        request.registry.settings["vitalsource_lti_launch_key"],
        request.registry.settings["vitalsource_lti_launch_secret"],
        request.registry.settings["vitalsource_api_key"],
    )
