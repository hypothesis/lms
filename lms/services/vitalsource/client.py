import re

import oauthlib
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_BODY

from lms.services.exceptions import ExternalRequestError
from lms.services.vitalsource._schemas import BookInfoSchema, BookTOCSchema

#: A regex for parsing the COURSE_ID and FILE_ID parts out of one of our custom
#: canvas://file/course/COURSE_ID/file_id/FILE_ID URLs.
DOCUMENT_URL_REGEX = re.compile(
    r"vitalsource:\/\/book\/bookID\/(?P<book_id>[^\/]*)\/cfi\/(?P<cfi>.*)"
)


class VitalSourceService:
    def __init__(self, http_service, lti_launch_key, lti_launch_secret, api_key):
        """
        Return a new VitalSourceService.

        :param lti_launch_key: OAuth consumer key
        :type lti_launch_key: str
        :param lti_launch_secret: OAuth consumer secret
        :type lti_launch_secret: str
        :raises ValueError: If credentials are invalid
        """
        if not all([lti_launch_key, lti_launch_secret, api_key]):
            raise ValueError("VitalSource credentials are missing")

        self._http_service = http_service

        self._lti_launch_key = lti_launch_key
        self._lti_launch_secret = lti_launch_secret
        self._api_key = api_key

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

        return BookTOCSchema(response).parse()

    @staticmethod
    def parse_document_url(document_url):
        return DOCUMENT_URL_REGEX.search(document_url).groupdict()

    def get_launch_params(self, document_url, lti_user):
        """
        Return the form params needed to launch the VitalSource book viewer.

        The VitalSource book viewer is launched using an LTI launch. This involves
        posting an HTML form containing the book ID and location along with metadata
        about the current user and an OAuth 1.0 signature.

        See https://developer.vitalsource.com/hc/en-us/articles/215612237-POST-LTI-Create-a-Bookshelf-Launch

        :param document_url: `vitalsource://` type URL identifying the document.
        :param lti_user: Current LTI user information, from the LTI launch request
        :type lti_user: LTIUser
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
