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

    @property
    def token_url(self):
        """
        Return the URL of the Canvas API's token endpoint.

        This is the OAuth 2.0 endpoint that you post an authorization code to
        in order to get an access token. See:

        https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token

        :rtype: str
        """
        return urlunparse(("https", self._canvas_url, "login/oauth2/token", "", "", ""))

    def list_files_url(self, course_id):
        """
        Return a Canvas list files API URL for ``course_id``.

        This is the API that returns a list of all the files in a course. See:

        https://canvas.instructure.com/doc/api/files.html#method.files.api_index

        :rtype: str
        """
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

    def access_token_request(self, authorization_code):
        """
        Return a prepared access token request.

        Return a prepared request object that, when sent, will make a
        server-to-server request to the Canvas API's token endpoint in order to
        exchange ``authorization_code`` for an access token.

        The request can be sent like this::

            >>> response = requests.Session().send(request)

        For documentation of this request see:

        https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token

        :arg authorization_code: the authorization code received from the
            browser after Canvas redirected the browser to our redirect_uri

        :rtype: requests.PreparedRequest
        """
        return requests.Request(
            "POST",
            self.token_url,
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

        The returned request, when sent, will make a server-to-server request
        to Canvas's list files API to get a list of the files belonging to
        ``course_id``.

        The request can be sent like this::

            >>> response = requests.Session().send(request)

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
            self.list_files_url(course_id),
            headers={"Authorization": f"Bearer {access_token}"},
        ).prepare()
