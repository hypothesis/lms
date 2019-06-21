import datetime

import requests
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIError
from lms.services.exceptions import CanvasAPIServerError
from lms.services._helpers import CanvasAPIHelper
from lms.validation import CanvasAccessTokenResponseSchema, ValidationError


__all__ = ["CanvasAPIClient"]


class CanvasAPIClient:
    def __init__(self, _context, request):
        self._helper = CanvasAPIHelper(
            request.lti_user.oauth_consumer_key,
            request.find_service(name="ai_getter"),
            request.route_url,
        )
        self._lti_user = request.lti_user
        self._db = request.db

    def get_token(self, authorization_code):
        """
        Get an access token for the current LTI user.

        Posts to the Canvas API to get the access token and returns it.

        :arg authorization_code: The Canvas API OAuth 2.0 authorization code to
            exchange for an access token
        :type authorization_code: str

        :raise lms.services.CanvasAPIServerError: if the Canvas API request
            fails for any reason
        """
        access_token_request = self._helper.access_token_request(authorization_code)

        try:
            access_token_response = requests.Session().send(access_token_request)
            access_token_response.raise_for_status()
        except RequestException as err:
            raise CanvasAPIServerError(
                explanation="Authorizing with Canvas failed",
                response=getattr(err, "response", None),
            ) from err

        try:
            parsed_params = CanvasAccessTokenResponseSchema(
                access_token_response
            ).parse()
        except ValidationError as err:
            raise CanvasAPIServerError(
                explanation=str(err), response=access_token_response
            ) from err

        access_token = parsed_params["access_token"]
        refresh_token = parsed_params.get("refresh_token")
        expires_in = parsed_params.get("expires_in")

        return (access_token, refresh_token, expires_in)

    def save_token(self, access_token, refresh_token=None, expires_in=None):
        # Find the existing token in the DB.
        token = (
            self._db.query(OAuth2Token)
            .filter_by(
                consumer_key=self._lti_user.oauth_consumer_key,
                user_id=self._lti_user.user_id,
            )
            .one_or_none()
        )

        # If there's no existing token in the DB then create a new one.
        if token is None:
            token = OAuth2Token()
            self._db.add(token)

        # Either update the existing token, or set the attributes of the newly
        # created one.
        token.consumer_key = self._lti_user.oauth_consumer_key
        token.user_id = self._lti_user.user_id
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.expires_in = expires_in
        token.received_at = datetime.datetime.utcnow()

    def list_files(self, course_id):
        """
        Return the list of files for the given ``course_id``.

        Send an HTTP request to the Canvas API to get the list of files, and
        return the list of files.

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :rtype: list(dict)
        """
        list_files_request = self._helper.list_files_request(
            self._access_token, course_id
        )
        list_files_response = requests.Session().send(list_files_request)

        # TODO: Validate list_files_response
        # TODO: Handle Canvas list files API error responses (for example an
        #       authorization error might require us to refresh the access
        #       token and try again)

        def present_file(file_dict):
            return {
                "id": file_dict["id"],
                "display_name": file_dict["display_name"],
                "updated_at": file_dict["updated_at"],
            }

        return [present_file(file_dict) for file_dict in list_files_response.json()]

    def public_url(self, file_id):
        """
        Return a new public download URL for the file with the given ID.

        Send an HTTP request to the Canvas API to get a new temporary public
        download URL, and return the URL.

        :arg file_id: the ID of the Canvas file
        :type file_id: str

        :rtype: str
        """
        public_url_request = self._helper.public_url_request(
            self._access_token, file_id
        )

        try:
            public_url_response = requests.Session().send(public_url_request)
            public_url_response.raise_for_status()
        except RequestException as err:
            # TODO: Try refreshing the access token and re-trying the response.
            response = getattr(err, "response", None)

            raise CanvasAPIError(
                explanation="Connecting to the Canvas API failed", response=response
            ) from err

        # TODO: Validate public_url_response

        return public_url_response.json()["public_url"]

    @property
    def _access_token(self):
        """Return the user's saved access token from the DB."""
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(
                    consumer_key=self._lti_user.oauth_consumer_key,
                    user_id=self._lti_user.user_id,
                )
                .one()
                .access_token
            )
        except NoResultFound as err:
            raise CanvasAPIError(
                explanation="We don't have a Canvas API access token for this user",
                response=None,
            ) from err
