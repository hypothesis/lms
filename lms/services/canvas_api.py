import datetime
from urllib.parse import urlencode, urlparse

import requests
from requests import RequestException
from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError
from lms.services.exceptions import CanvasAPIError
from lms.validation import (
    CanvasAuthenticatedUsersSectionsResponseSchema,
    CanvasCourseSectionsResponseSchema,
    CanvasListFilesResponseSchema,
    CanvasPublicURLResponseSchema,
    CanvasUsersSectionsResponseSchema,
    ValidationError,
)
from lms.validation.authentication import (
    CanvasAccessTokenResponseSchema,
    CanvasRefreshTokenResponseSchema,
)

__all__ = ["CanvasAPIClient"]


class CanvasAPIClient:
    def __init__(self, _context, request):
        ai_getter = request.find_service(name="ai_getter")

        self._client_id = ai_getter.developer_key()
        self._client_secret = ai_getter.developer_secret()
        self._canvas_url = urlparse(ai_getter.lms_url()).netloc
        self._redirect_uri = request.route_url("canvas_oauth_callback")

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
        response = self._validated_response(
            self._access_token_request(authorization_code),
            CanvasAccessTokenResponseSchema,
        )

        self._save(
            response.parsed_params["access_token"],
            response.parsed_params.get("refresh_token"),
            response.parsed_params.get("expires_in"),
        )

    def _access_token_request(self, authorization_code):
        """
        Return a prepared access token request.

        Return a server-to-server request to the Canvas API's token endpoint
        that exchanges ``authorization_code`` for an access token.

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token

        :arg authorization_code: the authorization code received from the
            browser after Canvas redirected the browser to our redirect_uri

        :rtype: requests.PreparedRequest
        """
        return requests.Request(
            "POST",
            self._token_url,
            params={
                "grant_type": "authorization_code",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": self._redirect_uri,
                "code": authorization_code,
                "replace_tokens": True,
            },
        ).prepare()

    def get_refreshed_token(self, refresh_token):
        response = self._validated_response(
            self._refresh_token_request(refresh_token),
            CanvasRefreshTokenResponseSchema,
        )

        new_access_token = response.parsed_params["access_token"]

        self._save(
            new_access_token,
            response.parsed_params.get("refresh_token", refresh_token),
            response.parsed_params.get("expires_in"),
        )

        return new_access_token

    def _refresh_token_request(self, refresh_token):
        return requests.Request(
            "POST",
            self._token_url,
            params={
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": refresh_token,
            },
        ).prepare()

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
            self._authenticated_users_sections_request(
                oauth2_token.access_token, course_id
            ),
            CanvasAuthenticatedUsersSectionsResponseSchema,
            oauth2_token.refresh_token,
        )

    def _authenticated_users_sections_request(self, access_token, course_id):
        """
        Return a prepared "authenticated users sections" request.

        Return a server-to-server request to the Canvas API that gets a list of
        the authenticated user's sections for the given course (course_id).

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/courses.html#method.courses.index

        :arg access_token: the access token to authenticate the request with
        :type access_token: str

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :rtype: requests.PreparedRequest
        """
        # Canvas's sections API
        # (https://canvas.instructure.com/doc/api/sections.html) only allows
        # you to get _all_ of a course's sections, it doesn't provide a way to
        # get only the sections that the authenticated user belongs to. So we
        # have to get the authenticated user's sections from part of the
        # response from a courses API endpoint instead.
        #
        # Canvas's "Get a single course" API is capable of doing this if the
        # ?include[]=sections query param is given:
        #
        #    https://canvas.instructure.com/doc/api/courses.html#method.courses.show
        #
        # The ?include[]=sections query param is documented elsewhere (in the
        # "List your courses" API:
        # https://canvas.instructure.com/doc/api/courses.html#method.courses.index)
        # as:
        #
        #    "Section enrollment information to include with each Course.
        #    Returns an array of hashes containing the section ID (id), section
        #    name (name), start and end dates (start_at, end_at), as well as the
        #    enrollment type (enrollment_role, e.g. 'StudentEnrollment')."
        #
        # In practice ?include[]=sections seems to add a "sections" key to the
        # API response that is a list of section dicts, one for each section
        # the authenticated user is currently enrolled in, each with the
        # section's "id" and "name" among other fields.
        #
        # **We don't know what happens if the user belongs to a really large
        # number of sections**. Does the list of sections embedded within the
        # get course API response just get really long? Does it get truncated?
        # Can you paginate through it somehow? This seems edge-casey enough
        # that we're ignoring it for now.

        return requests.Request(
            "GET",
            self._get_url(f"courses/{course_id}", params={"include[]": "sections"}),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

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
            self._course_sections_request(oauth2_token.access_token, course_id),
            CanvasCourseSectionsResponseSchema,
            oauth2_token.refresh_token,
        )

    def _course_sections_request(self, access_token, course_id):
        """
        Return a prepared "list course sections" request.

        Return a server-to-server request to the Canvas API that gets a list of
        all the sections for the given course (course_id).

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/sections.html#method.sections.index

        :arg access_token: the access token to authenticate the request with
        :type access_token: str

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :rtype: requests.PreparedRequest
        """

        return requests.Request(
            "GET",
            self._get_url(f"courses/{course_id}/sections"),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

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
            self._users_sections_request(oauth2_token.access_token, user_id, course_id),
            CanvasUsersSectionsResponseSchema,
            oauth2_token.refresh_token,
        )

    def _users_sections_request(self, access_token, user_id, course_id):
        """
        Return a prepared "user's course sections" request.

        Return a server-to-server request to the Canvas API that gets a list of
        all the given user's (user_id) sections for the given course
        (course_id).

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/courses.html#method.courses.user

        :arg access_token: the access token to authenticate the request with
        :type access_token: str

        :arg user_id: the Canvas user_id of the user whose sections you want
        :type user_id: str

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :rtype: requests.PreparedRequest
        """

        return requests.Request(
            "GET",
            self._get_url(
                f"courses/{course_id}/users/{user_id}",
                params={"include[]": "enrollments"},
            ),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

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
            self._list_files_request(oauth2_token.access_token, course_id),
            CanvasListFilesResponseSchema,
            oauth2_token.refresh_token,
        )

    def _list_files_request(self, access_token, course_id):
        """
        Return a prepared list files request.

        Return a server-to-server request to Canvas's list files API that gets
        a list of the files belonging to ``course_id``.

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/files.html#method.files.api_index

        :arg access_token: the access token to authenticate the request with
        :type access_token: str

        :arg course_id: the Canvas course_id of the course to look in
        :type course_id: str

        :rtype: requests.PreparedRequest
        """

        return requests.Request(
            "GET",
            self._get_url(
                f"courses/{course_id}/files",
                params={"content_types[]": "application/pdf", "per_page": 100},
            ),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

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
            self._public_url_request(oauth2_token.access_token, file_id),
            CanvasPublicURLResponseSchema,
            oauth2_token.refresh_token,
        )["public_url"]

    def _public_url_request(self, access_token, file_id):
        """
        Return a prepared public URL request.

        Return a server-to-server request to Canvas's file public URL API that
        gets a public download URL for the file with ID ``file_id``.

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/files.html#method.files.public_url

        :arg access_token: the access token to authenticate the request with
        :type access_token: str

        :arg file_id: the Canvas file ID of the file
        :type file_id: str

        :rtype: requests.PreparedRequest
        """

        return requests.Request(
            "GET",
            self._get_url(f"files/{file_id}/public_url"),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    def send_with_refresh_and_retry(self, request, schema, refresh_token):
        try:
            return self._validated_response(request, schema).parsed_params
        except CanvasAPIAccessTokenError:
            if not refresh_token:
                raise

            new_access_token = self.get_refreshed_token(refresh_token)
            return self._validated_response(
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

    @staticmethod
    def _validated_response(request, schema=None, access_token=None):
        """
        Send a Canvas API request and validate and return the response.

        If a validation schema is given then the parsed and validated response
        params will be available on the returned response object as
        ``response.parsed_params`` (a dict).

        :arg request: a prepared request to some Canvas API endoint
        :type request: requests.PreparedRequest

        :arg schema: The schema class to validate the contents of the response
          with. If this is ``None`` then the response contents won't be
          validated and there'll be no ``response.parsed_params``, but it will
          still test that a response was received (no network error or timeout)
          and the response had a 2xx HTTP status.
        :type schema: a subclass of :cls:`lms.validation.RequestsResponseSchema`

        :arg access_token: the access token to use in the
            "Authorization: Bearer <ACCESS_TOKEN>" header to authorize the
            request
        :type access_token: str

        :raise lms.services.CanvasAPIAccessTokenError: if the request fails
            because our Canvas API access token for the user is missing,
            expired, or has been deleted

        :raise lms.services.CanvasAPIServerError: if the request fails for any
            other reason (network error or timeout, non-2xx response received,
            2xx but invalid response received, etc)

        :rtype: requests.Response
        """
        if access_token:
            request.headers["Authorization"] = f"Bearer {access_token}"

        try:
            response = requests.Session().send(request, timeout=9)
            response.raise_for_status()
        except RequestException as err:
            CanvasAPIError.raise_from(err)

        if schema:
            try:
                response.parsed_params = schema(response).parse()
            except ValidationError as err:
                CanvasAPIError.raise_from(err)

        return response

    def _get_url(self, path, params=None, url_stub="/api/v1"):
        return f"https://{self._canvas_url}{url_stub}/{path}" + (
            "?" + urlencode(params) if params else ""
        )

    @property
    def _token_url(self):
        """Return the URL of the Canvas API's token endpoint."""

        return self._get_url("login/oauth2/token", url_stub="")
