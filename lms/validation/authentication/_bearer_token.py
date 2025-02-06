"""Schema for our bearer token-based LTI authentication."""

from datetime import timedelta

import marshmallow

from lms.models import LTIUser
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService
from lms.services.lti_user import LTIUserService
from lms.validation import ValidationError
from lms.validation._base import PyramidRequestSchema

__all__ = ("BearerTokenSchema",)


class BearerTokenSchema(PyramidRequestSchema):
    """
    Schema for our bearer token-based LTI authentication.

    Serializes models.LTIUser objects into signed and
    timestamped ``"Bearer <ENCODED_JWT>"`` strings, and deserializes these
    bearer strings back into models.LTIUser objects. The
    JWT signature and timestamp are verified during deserialization.

    Usage:

        >>> schema = BearerTokenSchema(request)

        >>> # Serialize an LTIUser (``request.lti_user`` in this example)
        >>> # into an authorization param value:
        >>> schema.authorization_param(request.lti_user)
        'Bearer eyJ...YoM'

        >>> # Deserialize the request's authorization param into an LTI user.
        >>> schema.lti_user(location='headers')
        LTIUser(user_id='...', application_instance_id='...', ...)
    """

    authorization = marshmallow.fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)
        self._jwt_service: JWTService = request.find_service(iface=JWTService)
        self._lti_user_service = request.find_service(iface=LTIUserService)
        self._secret = request.registry.settings["jwt_secret"]

    def authorization_param(
        self, lti_user: LTIUser, lifetime: timedelta = timedelta(hours=24)
    ) -> str:
        """
        Return ``lti_user`` serialized into an authorization param.

        Returns a ``"Bearer: <ENCODED_JWT>"`` string suitable for use as the
        value of an authorization param.

        :arg lti_user: the LTI user to return an auth param for
        :arg lifetime: how long the token should be valid for
        """
        token = self._jwt_service.encode_with_secret(
            self._lti_user_service.serialize(lti_user) if lti_user else {},
            self._secret,
            lifetime=lifetime,
        )

        return f"Bearer {token}"

    def lti_user(self, location) -> LTIUser:
        """
        Return a models.LTIUser from the request's authorization param.

        Verifies the signature and timestamp of the JWT in the request's
        authorization param, decodes the JWT, validates the JWT's payload, and
        returns a models.LTIUser from the payload.

        The authorization param can be in an HTTP header
        ``Authorization: Bearer <ENCODED_JWT>``, in a query string parameter
        ``?authorization=Bearer%20<ENCODED_JWT>``, or in a form field
        ``authorization=Bearer+<ENCODED_JWT>``. In the future we may add
        support for reading the authorization param from other parts of the
        request, such as from JSON body fields.

        :raise ExpiredSessionTokenError: if the request's Authorization header
          contains an expired JWT
        :raise MissingSessionTokenError: if the request does not contain an
          Authorization header
        :raise InvalidSessionTokenError: if the request contains an invalid
          Authorization header. For example if the Authorization header
          contains an invalid JWT, or if it doesn't have the required
          ``"Bearer <ENCODED_JWT>"`` format.
        :raise ValidationError: if the JWT's payload is invalid, for example if
          it's missing a required parameter
        """
        try:
            jwt_data = self._jwt_service.decode_with_secret(
                # Get the authorization param from the right location
                self.parse(location=location)["authorization"],
                self._secret,
            )
        except ExpiredJWTError as err:
            raise ValidationError(
                messages={"authorization": ["Expired session token"]}
            ) from err

        except InvalidJWTError as err:
            raise ValidationError(
                messages={"authorization": ["Invalid session token"]}
            ) from err

        return self._lti_user_service.deserialize(**jwt_data)

    @marshmallow.pre_load
    def _decode_authorization(self, data, **_kwargs):
        """Return the payload from the JWT in the authorization param in ``data``."""
        if data["authorization"] == marshmallow.missing:
            raise ValidationError(
                messages={"authorization": ["Missing data for required field."]}
            )

        jwt = data["authorization"]
        # Some locations (cookies) don't allow the leading "Bearer " so we don't include it.
        # Remove it in all other cases
        jwt = jwt.removeprefix("Bearer ")
        return {"authorization": jwt}
