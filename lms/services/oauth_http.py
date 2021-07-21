from lms.validation.authentication import OAuthTokenResponseSchema


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

    def get_access_token(self, token_url, redirect_uri, auth, authorization_code):
        """
        Make an access token request and save the token in the DB.

        Send an OAuth 2.0 "access token request"
        (https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.3) to get a
        new access token for the current user and save it to the DB.

        :raise HTTPError: if the HTTP request fails
        :raise ValidationError: if the server's access token response is invalid
        """
        self._token_request(
            token_url=token_url,
            auth=auth,
            data={
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": authorization_code,
            },
        )

    def _token_request(self, token_url, data, auth):
        response = self._http_service.post(token_url, data=data, auth=auth)

        validated_data = OAuthTokenResponseSchema(response).parse()

        self._oauth2_token_service.save(
            validated_data["access_token"],
            validated_data.get("refresh_token"),
            # pylint:disable=no-member
            validated_data.get("expires_in"),
        )

        return validated_data["access_token"]


def factory(_context, request):
    return OAuthHTTPService(
        request.find_service(name="http"), request.find_service(name="oauth2_token")
    )
