"""Helpers for working with the Canvas API."""
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from requests import RequestException

from lms.services.exceptions import CanvasAPIError
from lms.validation import ValidationError

__all__ = ["CanvasAPIHelper"]


class CanvasAPIHelper:
    """
    Methods for generating useful Canvas API values.

    A lot of working with the Canvas API is generating correct values. For
    example generating the token endpoint URL for the right Canvas instance, or
    generating an access token request with the right URL, HTTP verb and
    parameters.

    This helper handles generating these kinds of values so that the higher
    level code can focus on what to *do* with the values instead.

    Objects of this class are immutable, and none of their properties or
    methods have any side effects.

    Many of the returned values are :class:`requests.PreparedRequest` objects.
    These are HTTP requests prepared with the right URL, headers and params.
    They can be sent like this::

        >>> response = requests.Session().send(prepared_request)
    """

    def __init__(self, consumer_key, ai_getter, route_url):
        """
        Initialize a CanvasAPIHelper for the given ``consumer_key``.

        :arg consumer_key: the consumer key of the application instance whose
            Canvas instance's API we're going to be using
        :type consumer_key: str

        :arg ai_getter: the "ai_getter" service

        :arg route_url: the :meth:`pyramid.request.Request.route_url()` method
        :type route_url: callable
        """
        self._client_id = ai_getter.developer_key(consumer_key)
        self._client_secret = ai_getter.developer_secret(consumer_key)
        self._canvas_url = urlparse(ai_getter.lms_url(consumer_key)).netloc
        self._redirect_uri = route_url("canvas_oauth_callback")

    def access_token_request(self, authorization_code):
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

    def refresh_token_request(self, refresh_token):
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

    def authenticated_users_sections_request(self, access_token, course_id):
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
        url = urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/courses/{course_id}",
                "",
                "include[]=sections",
                "",
            )
        )

        return requests.Request(
            "GET", url, headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    def course_sections_request(self, access_token, course_id):
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
        url = urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/courses/{course_id}/sections",
                "",
                "",
                "",
            )
        )

        return requests.Request(
            "GET", url, headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    def users_sections_request(self, access_token, user_id, course_id):
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
        url = urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/courses/{course_id}/users/{user_id}",
                "",
                "include[]=enrollments",
                "",
            )
        )

        return requests.Request(
            "GET", url, headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    def list_files_request(self, access_token, course_id):
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
        url = urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/courses/{course_id}/files",
                "",
                urlencode({"content_types[]": "application/pdf", "per_page": 100}),
                "",
            )
        )

        return requests.Request(
            "GET", url, headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    def public_url_request(self, access_token, file_id):
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
        url = urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/files/{file_id}/public_url",
                "",
                "",
                "",
            )
        )

        return requests.Request(
            "GET", url, headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    @staticmethod
    def validated_response(request, schema=None, access_token=None):
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

    @property
    def _token_url(self):
        """Return the URL of the Canvas API's token endpoint."""
        return urlunparse(("https", self._canvas_url, "login/oauth2/token", "", "", ""))
