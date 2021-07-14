from lms.services import HTTPError


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

    def request(self, method, url, refresh=None, **kwargs):
        oauth2_token = self._oauth2_token_service.get()
        access_token = oauth2_token.access_token
        refresh_token = oauth2_token.refresh_token

        kwargs.setdefault("headers", {})
        assert "Authorization" not in kwargs["headers"]

        def send_request():
            kwargs["headers"]["Authorization"] = f"Bearer {access_token}"
            return self._http_service.request(method, url, **kwargs)

        try:
            return send_request()
        except HTTPError:
            if not refresh_token or not refresh:
                raise

        access_token = refresh(refresh_token=refresh_token)

        return send_request()


def factory(_context, request):
    return OAuthHTTPService(
        request.find_service(name="http"), request.find_service(name="oauth2_token")
    )
