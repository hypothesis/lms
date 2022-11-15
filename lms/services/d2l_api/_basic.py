from lms.services.exceptions import ExternalRequestError

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
            err.refreshable = getattr(err.response, "status_code", None) == 401
            raise

    def api_url(self, path, product="lp"):
        """
        Get the full API.

        :param path: relative path of the endpoint.
        :param product: product within the D2L api

            https://docs.valence.desire2learn.com/basic/conventions.html#term-D2LPRODUCT
        """
        return f"https://{self.lms_host}/d2l/api/{product}/{API_VERSION}{path}"
