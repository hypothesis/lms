from marshmallow import INCLUDE, fields

from lms.services.exceptions import HTTPError, OAuth2TokenError
from lms.validation import RequestsResponseSchema, ValidationError


class BlackboardErrorResponseSchema(RequestsResponseSchema):
    """
    Schema for validating error responses from the Blackboard API.

    This schema's parse() method will return the given response's JSON body as
    a dict (with whatever fields the response body from Blackboard had) and
    will default to returning an empty dict if the given response's body isn't
    a JSON dict, or isn't a dict at all, or if the response isn't a
    requests.Response object (e.g. if it's None).

    """

    # Blackboard API error bodies have a "status" key whose value is the
    # response's HTTP status code as an int.
    #
    # This schema is permissive and doesn't guarantee that the dict returned
    # from parse() will have a "status" or that "status"'s value will be an
    # int.
    status = fields.Raw(required=False, allow_none=True)

    # Blackboard API error bodies have a "message" key whose value is a
    # human-readable error message string.
    #
    # This schema is permissive and doesn't guarantee that the dict returned
    # from parse() will have a "message" or that "message"'s value will be a
    # string.
    message = fields.Raw(required=False, allow_none=True)

    class Meta:
        unknown = INCLUDE

    def parse(self, *args, **kwargs):
        try:
            return super().parse(*args, **kwargs)
        except ValidationError:
            return {}


class BasicClient:
    """A low-level Blackboard API client."""

    def __init__(
        self,
        blackboard_host,
        client_id,
        client_secret,
        redirect_uri,
        http_service,
        oauth_http_service,
    ):  # pylint:disable=too-many-arguments
        self.blackboard_host = blackboard_host
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        self._http_service = http_service
        self._oauth_http_service = oauth_http_service

    def get_token(self, authorization_code):
        self._oauth_http_service.get_access_token(
            token_url=self.token_url,
            redirect_uri=self.redirect_uri,
            auth=(self.client_id, self.client_secret),
            authorization_code=authorization_code,
        )

    def request(self, method, path):
        url = self._api_url(path)

        try:
            return self._send(method, url)
        except (OAuth2TokenError, HTTPError):
            self._oauth_http_service.refresh_access_token(
                self.token_url,
                self.redirect_uri,
                auth=(self.client_id, self.client_secret),
            )
            return self._send(method, url)

    @property
    def token_url(self):
        return self._api_url("oauth2/token")

    def _api_url(self, path):
        """Return the full Blackboard API URL for the given path."""

        if not path.startswith("/"):
            # Paths that don't start with "/" are treated as relative to this
            # common Blackboard API path prefix.
            path = "/learn/api/public/v1/" + path

        return f"https://{self.blackboard_host}{path}"

    def _send(self, method, url):
        try:
            return self._oauth_http_service.request(method, url)
        except HTTPError as err:
            error_dict = BlackboardErrorResponseSchema(err.response).parse()

            if error_dict.get("message") == "Bearer token is invalid":
                raise OAuth2TokenError() from err

            raise
