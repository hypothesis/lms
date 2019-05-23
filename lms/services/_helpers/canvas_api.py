"""Helpers for working with the Canvas API."""
from urllib.parse import urlencode, urlparse, urlunparse

import requests


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
            },
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
        return requests.Request(
            "GET",
            self._list_files_url(course_id),
            headers={"Authorization": f"Bearer {access_token}"},
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
        return requests.Request(
            "GET",
            self._public_url(file_id),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()

    @property
    def _token_url(self):
        """Return the URL of the Canvas API's token endpoint."""
        return urlunparse(("https", self._canvas_url, "login/oauth2/token", "", "", ""))

    def _list_files_url(self, course_id):
        """Return the Canvas list files API URL for ``course_id``."""
        return urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/courses/{course_id}/files",
                "",
                urlencode({"content_types[]": "application/pdf", "per_page": 100}),
                "",
            )
        )

    def _public_url(self, file_id):
        """Return a URL for Canvas's file public URL API."""
        return urlunparse(
            (
                "https",
                self._canvas_url,
                f"/api/v1/files/{file_id}/public_url",
                "",
                "",
                "",
            )
        )
