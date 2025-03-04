import secrets
from datetime import timedelta

import marshmallow
from webargs import fields

from lms.models import LTIUser
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService
from lms.services.lti_user import LTIUserService
from lms.validation._base import PyramidRequestSchema, RequestsResponseSchema
from lms.validation.authentication._exceptions import (
    ExpiredStateParamError,
    InvalidStateParamError,
    MissingStateParamError,
)


class OAuthCallbackSchema(PyramidRequestSchema):
    """
    Schema for validating OAuth 2 redirect_uri requests.

    This schema provides two convenience methods:

    First, :meth:`OAuthCallbackSchema.state_param` returns a string
    suitable for passing to an authorization server's authorization endpoint as
    the ``state`` query parameter::

       >>> schema = OAuthCallbackSchema()
       >>> schema._request = request
       >>> schema.state_param(request.lti_user)
       'xyz...123'

    Calling :meth:`OAuthCallbackSchema.state_param` also has the side
    effect of inserting a CSRF token into the session that will be checked
    against the ``state`` parameter when the authorization server returns the
    ``state`` parameter to us in a later ``redirect_uri`` request.

    Second, :meth:`OAuthCallbackSchema.lti_user` returns the
    models.LTIUser authenticated by the ``state`` param in the
    current request. This will raise if the request doesn't contain a ``state``
    query parameter or if the ``state`` is expired or invalid::

       >>> schema.lti_user()
       LTIUser(user_id='...', oauth_consumer_key='...')

    Finally, :class:`OAuthCallbackSchema` can also be used as a schema to
    guard a ``redirect_uri`` view, for example::

        @view_config(..., schema=OAuthCallbackSchema)
        def redirect_uri_view(request):
            # The authorization code and state sent by the authorization server
            # are available in request.parsed_params.
            authorization_code = request.parsed_params["code"]
            state = request.parsed_params["state"]
            ...

    This will prevent the view from being called if the code or state is
    missing, if the state is invalid or expired, or if there isn't a matching
    CSRF token in the session, and it will remove the CSRF token from the
    session so that it can't be reused.
    """

    location = "querystring"
    code = fields.Str(required=True)
    state = fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)
        self._secret = request.registry.settings["oauth2_state_secret"]
        self._jwt_service = request.find_service(iface=JWTService)
        self._lti_user_service = request.find_service(iface=LTIUserService)

    def state_param(self):
        """
        Generate and return the value for an OAuth 2 state param.

        :rtype: str
        """
        csrf = secrets.token_hex()

        data = {
            "user": self._lti_user_service.serialize(self._request.lti_user),
            "csrf": csrf,
        }

        jwt_str = self._jwt_service.encode_with_secret(
            data, self._secret, lifetime=timedelta(hours=1)
        )

        self._request.session["oauth2_csrf"] = csrf

        return jwt_str

    def lti_user(self, state=None) -> LTIUser:
        """
        Return the LTIUser authenticated by state data in an OAuth callback.

        If ``state`` is None, the state is obtained from the current request's
        ``state`` query parameter.

        :raise MissingStateParamError: if the request has no ``state`` query
            parameter
        :raise ExpiredStateParamError: if the state has expired
        :raise InvalidStateParamError: if the state is invalid
        """

        if state is None:
            try:
                state = self._request.params["state"]
            except KeyError as err:
                raise MissingStateParamError() from err  # noqa: RSE102

        decoded_user = self._decode_state(state)["user"]
        return self._lti_user_service.deserialize(**decoded_user)

    @marshmallow.validates("state")
    def validate_state(self, state):
        """Validate the current request's ``state`` param."""
        payload = self._decode_state(state)

        if payload["csrf"] != self._request.session.pop("oauth2_csrf", None):
            raise marshmallow.ValidationError("Invalid CSRF token")  # noqa: EM101, TRY003

    def _decode_state(self, state):
        """Decode the given state JWT and return its payload or raise."""
        try:
            return self._jwt_service.decode_with_secret(state, self._secret)
        except ExpiredJWTError as err:
            raise ExpiredStateParamError() from err  # noqa: RSE102
        except InvalidJWTError as err:
            raise InvalidStateParamError() from err  # noqa: RSE102


class OAuthTokenResponseSchema(RequestsResponseSchema):
    """Schema for token responses from OAuth 2 authentication servers."""

    access_token = fields.Str(required=True)
    refresh_token = fields.Str()
    expires_in = fields.Integer(validate=marshmallow.validate.Range(min=1))
