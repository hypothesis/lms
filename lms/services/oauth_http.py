class OAuthHTTPService:
    """Send OAuth 2.0 requests and return the responses."""

    def __init__(self, http_service, oauth2_token_service):
        self._http_service = http_service
        self._oauth2_token_service = oauth2_token_service

    def get(self, *args, **kwargs):
        return self.request("GET", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request("PUT", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("POST", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request("PATCH", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("DELETE", *args, **kwargs)

    def request(self, method, url, headers=None, **kwargs):
        """
        Send an access token-authenticated request and return the response.

        This will look up the user's access token in the DB and insert it into
        the `headers` dict as an OAuth 2-formatted "Authorization" header.
        Otherwise this method behaves the same as HTTPService.request().

        The given `headers` must not already contain an "Authorization" header.

        :raise OAuth2TokenError: if we don't have an access token for the user
        :raise HTTPError: if something goes wrong with the HTTP request
        """
        headers = headers or {}

        assert "Authorization" not in headers

        access_token = self._oauth2_token_service.get().access_token
        headers["Authorization"] = f"Bearer {access_token}"

        return self._http_service.request(method, url, headers=headers, **kwargs)


def factory(_context, request):
    return OAuthHTTPService(
        request.find_service(name="http"), request.find_service(name="oauth2_token")
    )
