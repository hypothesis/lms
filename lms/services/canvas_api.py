import datetime

from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError
from lms.services._helpers import CanvasAPIHelper
from lms.validation import (
    CanvasAuthenticatedUsersSectionsResponseSchema,
    CanvasCourseSectionsResponseSchema,
    CanvasListFilesResponseSchema,
    CanvasPublicURLResponseSchema,
    CanvasUsersSectionsResponseSchema,
)
from lms.validation.authentication import (
    CanvasAccessTokenResponseSchema,
    CanvasRefreshTokenResponseSchema,
)

__all__ = ["CanvasAPIClient"]


class CanvasAPIClient:
    def __init__(self, _context, request):
        self._helper = CanvasAPIHelper(
            request.find_service(name="ai_getter"), request.route_url,
        )
        self._consumer_key = request.lti_user.oauth_consumer_key
        self._user_id = request.lti_user.user_id
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

        self._save(
            response.parsed_params["access_token"],
            response.parsed_params.get("refresh_token"),
            response.parsed_params.get("expires_in"),
        )

    def get_refreshed_token(self, refresh_token):
        response = self._helper.validated_response(
            self._helper.refresh_token_request(refresh_token),
            CanvasRefreshTokenResponseSchema,
        )

        new_access_token = response.parsed_params["access_token"]

        self._save(
            new_access_token,
            response.parsed_params.get("refresh_token", refresh_token),
            response.parsed_params.get("expires_in"),
        )

        return new_access_token

    def authenticated_users_sections(self, course_id):
        """
        Return the authenticated user's sections for the given course_id.

        Send an HTTP request to the Canvas API to get the list of sections and
        return it.

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :raise lms.services.CanvasAPIAccessTokenError: if we can't get the list
            of sections because we don't have a working Canvas API access token
            for the user
        :raise lms.services.CanvasAPIServerError: if we do have an access token
            but the Canvas API request fails for any other reason

        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """
        oauth2_token = self._oauth2_token

        return self.send_with_refresh_and_retry(
            self._helper.authenticated_users_sections_request(
                oauth2_token.access_token, course_id
            ),
            CanvasAuthenticatedUsersSectionsResponseSchema,
            oauth2_token.refresh_token,
        )

    def course_sections(self, course_id):
        """
        Return all the sections for the given course_id.

        Send an HTTP request to the Canvas API to get the list of sections and
        return it.

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :raise lms.services.CanvasAPIAccessTokenError: if we can't get the list
            of sections because we don't have a working Canvas API access token
            for the user
        :raise lms.services.CanvasAPIServerError: if we do have an access token
            but the Canvas API request fails for any other reason

        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """
        oauth2_token = self._oauth2_token

        return self.send_with_refresh_and_retry(
            self._helper.course_sections_request(oauth2_token.access_token, course_id),
            CanvasCourseSectionsResponseSchema,
            oauth2_token.refresh_token,
        )

    def users_sections(self, user_id, course_id):
        """
        Return all the given user's sections for the given course_id.

        Send an HTTP request to the Canvas API to get the list of sections and
        return it.

        :arg user_id: the Canvas user_id of the user whose sections you want
        :type user_id: str

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :raise lms.services.CanvasAPIAccessTokenError: if we can't get the list
            of sections because we don't have a working Canvas API access token
            for the user
        :raise lms.services.CanvasAPIServerError: if we do have an access token
            but the Canvas API request fails for any other reason

        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """
        oauth2_token = self._oauth2_token

        return self.send_with_refresh_and_retry(
            self._helper.users_sections_request(
                oauth2_token.access_token, user_id, course_id
            ),
            CanvasUsersSectionsResponseSchema,
            oauth2_token.refresh_token,
        )

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
        oauth2_token = self._oauth2_token

        return self.send_with_refresh_and_retry(
            self._helper.list_files_request(oauth2_token.access_token, course_id),
            CanvasListFilesResponseSchema,
            oauth2_token.refresh_token,
        )

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
        oauth2_token = self._oauth2_token

        return self.send_with_refresh_and_retry(
            self._helper.public_url_request(oauth2_token.access_token, file_id),
            CanvasPublicURLResponseSchema,
            oauth2_token.refresh_token,
        )["public_url"]

    def send_with_refresh_and_retry(self, request, schema, refresh_token):
        try:
            return self._helper.validated_response(request, schema).parsed_params
        except CanvasAPIAccessTokenError:
            if not refresh_token:
                raise

            new_access_token = self.get_refreshed_token(refresh_token)
            return self._helper.validated_response(
                request, schema, new_access_token
            ).parsed_params

    def _save(self, access_token, refresh_token, expires_in):
        """
        Save an access token and refresh token to the DB.

        If there's already an :class:`lms.models.OAuth2Token` for
        ``self._consumer_key`` and ``self._user_id`` then overwrite its values.
        Otherwise create a new :class:`lms.models.OAuth2Token` and add it to
        the DB.
        """
        try:
            oauth2_token = self._oauth2_token
        except CanvasAPIAccessTokenError:
            oauth2_token = OAuth2Token(
                consumer_key=self._consumer_key, user_id=self._user_id
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

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
                .filter_by(consumer_key=self._consumer_key, user_id=self._user_id)
                .one()
            )
        except NoResultFound as err:
            raise CanvasAPIAccessTokenError(
                explanation="We don't have a Canvas API access token for this user",
                response=None,
            ) from err
