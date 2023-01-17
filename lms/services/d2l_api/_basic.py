from lms.services.exceptions import ExternalRequestError, OAuth2TokenError

TOKEN_URL = "https://auth.brightspace.com/core/connect/token"
"""This is constant for all D2L instances"""


API_VERSION = "1.31"
"""Minimum, non deprecated version we can use for all needed endpoints"""


class BasicClient:
    """A low-level D2L API client."""

    def __init__(
        self,
        client_id,
        client_secret,
        lms_host,
        redirect_uri,
        http_service,
        oauth_http_service,
    ):  # pylint:disable=too-many-arguments
        self.lms_host = lms_host

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self._http_service = http_service
        self._oauth_http_service = oauth_http_service

    def get_token(self, authorization_code):
        """Get an oauth2 token and store it in the DB."""
        self._oauth_http_service.get_access_token(
            token_url=TOKEN_URL,
            redirect_uri=self.redirect_uri,
            auth=(self.client_id, self.client_secret),
            authorization_code=authorization_code,
        )

    def refresh_access_token(self):
        """Refresh and existing oauth2 token."""
        self._oauth_http_service.refresh_access_token(
            TOKEN_URL,
            self.redirect_uri,
            auth=(self.client_id, self.client_secret),
        )

    def request(self, method, path, **kwargs):
        """
        Make an API http request.

        :param method: HTTP method
        :param path: path of the endpoint.
            Relative paths are expanded by `BasicClient.api_url`. Absolute URLs are used verbatim.
        :param kwargs: extra arguments for the requests

        :raises ExternalRequestError: For any request based failure
        """
        if path.startswith("/"):
            path = self.api_url(path)

        try:
            return self._oauth_http_service.request(method, path, **kwargs)
        except ExternalRequestError as err:
            status_code = getattr(err.response, "status_code", None)
            response_text = getattr(err.response, "text", "")
            err.refreshable = status_code == 401

            if status_code == 403 and "Insufficient scope to call" in response_text:
                # This handles the case were the token was originally issued
                # for a set of scopes, a feature that needs extra scopes is
                # enabled, and a request for that feature fails.
                # Raising OAuth2TokenError re-starts the oauth2 flow, getting
                # a new token with the correct scopes. This won't handle the
                # case were the schools install doesn't have the required
                # scopes. In that case the request doesn't make its way our
                # server.
                raise OAuth2TokenError(refreshable=False) from err

            raise

    def api_url(self, path, product="lp"):
        """
        Get the full API.

        :param path: relative path of the endpoint.
        :param product: product within the D2L api

            https://docs.valence.desire2learn.com/basic/conventions.html#term-D2LPRODUCT
        """
        return f"https://{self.lms_host}/d2l/api/{product}/{API_VERSION}{path}"
