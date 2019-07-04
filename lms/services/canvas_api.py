import datetime

from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError
from lms.services._helpers import CanvasAPIHelper
from lms.validation import (
    CanvasAccessTokenResponseSchema,
    CanvasListFilesResponseSchema,
    CanvasPublicURLResponseSchema,
)


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
        response = self._helper.validated_response(
            self._helper.access_token_request(authorization_code),
            CanvasAccessTokenResponseSchema,
        )

        return (
            response.parsed_params["access_token"],
            response.parsed_params.get("refresh_token"),
            response.parsed_params.get("expires_in"),
        )

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

        :raise lms.services.CanvasAPIAccessTokenError: if we can't get the list
            of files because we don't have a working Canvas API access token
            for the user
        :raise lms.services.CanvasAPIServerError: if we do have an access token
            but the Canvas API request fails for any other reason

        :rtype: list(dict)
        """
        return self._helper.validated_response(
            self._helper.list_files_request(self._oauth2_token.access_token, course_id),
            CanvasListFilesResponseSchema,
        ).parsed_params

    def public_url(self, file_id):
        """
        Return a new public download URL for the file with the given ID.

        Send an HTTP request to the Canvas API to get a new temporary public
        download URL, and return the URL.

        :arg file_id: the ID of the Canvas file
        :type file_id: str

        :raise lms.services.CanvasAPIAccessTokenError: if we can't get the
            public URL because we don't have a working Canvas API access token
            for the user
        :raise lms.services.CanvasAPIServerError: if we do have an access token
            but the Canvas API request fails for any other reason

        :rtype: str
        """
        return self._helper.validated_response(
            self._helper.public_url_request(self._oauth2_token.access_token, file_id),
            CanvasPublicURLResponseSchema,
        ).parsed_params["public_url"]

    @property
    def _oauth2_token(self):
        """
        Return the user's saved access and refresh tokens from the DB.

        :raise lms.services.CanvasAPIAccessTokenError: if we don't have an access token
            for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(
                    consumer_key=self._lti_user.oauth_consumer_key,
                    user_id=self._lti_user.user_id,
                )
                .one()
            )
        except NoResultFound as err:
            raise CanvasAPIAccessTokenError(
                explanation="We don't have a Canvas API access token for this user",
                response=None,
            ) from err
