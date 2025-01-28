import logging
from datetime import datetime, timedelta

from marshmallow import fields

from lms.db import CouldNotAcquireLock
from lms.models.application_instance import ApplicationInstance
from lms.models.oauth2_token import Service
from lms.services.exceptions import (
    ConcurrentTokenRefreshError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.services.oauth2_token import OAuth2TokenService, oauth2_token_service_factory
from lms.validation import RequestsResponseSchema
from lms.validation.authentication import OAuthTokenResponseSchema

LOG = logging.getLogger(__name__)


class _OAuthAccessTokenErrorResponseSchema(RequestsResponseSchema):
    """Schema for parsing OAuth 2 access token error response bodies."""

    error = fields.String(required=True)


class OAuthHTTPService:
    """Send OAuth 2.0 requests and return the responses."""

    def __init__(
        self,
        http_service,
        oauth2_token_service: OAuth2TokenService,
        service: Service = Service.LMS,
    ):
        self._http_service = http_service
        self._oauth2_token_service = oauth2_token_service
        self.service = service

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
        :raise ExternalRequestError: if something goes wrong with the HTTP
            request
        """
        headers = headers or {}

        assert "Authorization" not in headers  # noqa: S101

        access_token = self._oauth2_token_service.get(service=self.service).access_token
        headers["Authorization"] = f"Bearer {access_token}"

        return self._http_service.request(method, url, headers=headers, **kwargs)

    def get_access_token(self, token_url, redirect_uri, auth, authorization_code):
        """
        Make an access token request and save the token in the DB.

        Send an OAuth 2.0 "access token request"
        (https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.3) to get a
        new access token for the current user and save it to the DB.

        :raise ExternalRequestError: if the HTTP request fails
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

    def refresh_access_token(
        self,
        token_url,
        redirect_uri,
        auth,
        prevent_concurrent_refreshes=True,  # noqa: FBT002
    ):
        """
        Make a refresh token request and save the new token in the DB.

        Send an OAuth 2.0 "refresh token request"
        (https://datatracker.ietf.org/doc/html/rfc6749#section-6) to get a new
        access token for the current user and save it to the DB.

        :raise ConcurrentTokenRefreshError: if the token could not be refreshed
            because another request is already refreshing it
        :raise OAuth2TokenError: if we don't have a refresh token for the user
        :raise ExternalRequestError: if the HTTP request fails
        :raise ValidationError: if the server's access token response is invalid
        """
        old_token = self._oauth2_token_service.get(self.service)

        # If the "old" token is already current, just return immediately.
        if (
            old_token.access_token
            and datetime.utcnow() - old_token.received_at < timedelta(seconds=30)  # noqa: DTZ003
        ):
            return old_token.access_token

        # Check for concurrent refresh attempts.
        try:
            self._oauth2_token_service.try_lock_for_refresh(self.service)
        except CouldNotAcquireLock as exc:
            LOG.debug('Concurrent OAuth token refresh with token URL "%s"', token_url)
            if prevent_concurrent_refreshes:
                # Prevent concurrent refresh attempts. If acquiring the lock
                # fails, the client should wait briefly and try again, at which
                # point it should find the refreshed token already available and
                # skip the refresh.
                raise ConcurrentTokenRefreshError() from exc  # noqa: RSE102

        try:
            return self._token_request(
                token_url=token_url,
                auth=auth,
                data={
                    "redirect_uri": redirect_uri,
                    "grant_type": "refresh_token",
                    "refresh_token": old_token.refresh_token,
                },
            )
        except ExternalRequestError as err:
            try:
                error_dict = _OAuthAccessTokenErrorResponseSchema(err.response).parse()
            except ExternalRequestError:
                pass
            else:
                if error_dict["error"] == "invalid_grant":
                    # Looks like our refresh token has expired or been revoked.
                    raise OAuth2TokenError() from err  # noqa: RSE102

            raise

    def _token_request(self, token_url, data, auth):
        response = self._http_service.post(token_url, data=data, auth=auth)

        validated_data = OAuthTokenResponseSchema(response).parse()

        self._oauth2_token_service.save(
            validated_data["access_token"],
            validated_data.get("refresh_token"),
            validated_data.get("expires_in"),
            service=self.service,
        )

        return validated_data["access_token"]


def factory(
    _context,
    request,
    service: Service = Service.LMS,
    application_instance: ApplicationInstance | None = None,
    user_id: str | None = None,
) -> OAuthHTTPService:
    """
    Create an `OAuthHTTPService`.

    :param request: The Pyramid request
    :param service: The API this service will communicate with
    :param user_id:
        The LTI user ID of the user whose API tokens should be used. Defaults
        to the LTI user from the current request.
    :param application_instance:
        Use API tokens associated with this application instance. Defaults to
        the application instance associated with the current request.
    """
    if user_id or application_instance:
        oauth2_token_svc = oauth2_token_service_factory(
            _context,
            request,
            application_instance=application_instance,
            user_id=user_id,
        )
    else:
        oauth2_token_svc = request.find_service(name="oauth2_token")
    return OAuthHTTPService(
        request.find_service(name="http"),
        oauth2_token_svc,
        service=service,
    )
