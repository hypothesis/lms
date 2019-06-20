"""Schema for validating LTI launch params."""
import marshmallow
from webargs.pyramidparser import parser
from pyramid.httpexceptions import HTTPUnprocessableEntity

from lms.services import LTILaunchVerificationError
from lms.validation._exceptions import ValidationError
from lms.validation._helpers import BaseSchema
from lms.values import LTIUser


__all__ = ("LaunchParamsSchema",)


class LaunchParamsSchema(BaseSchema):
    """
    Schema for LTI launch params.

    Validates and verifies LTI launch params. Usage via webargs::

        >>> from webargs.pyramidparser import parser
        >>>
        >>> schema = LaunchParamsSchema(request)
        >>> parsed_params = parser.parse(schema, request, locations=["form"])

    Or to verify the request and get an :class:`~lms.values.LTIUser`
    from the request's params::

        >>> schema = LaunchParamsSchema(request)
        >>> schema.lti_user()
        LTIUser(user_id='...', ...)
    """

    user_id = marshmallow.fields.Str(required=True)
    roles = marshmallow.fields.Str(required=True)

    oauth_consumer_key = marshmallow.fields.Str(required=True)
    oauth_nonce = marshmallow.fields.Str(required=True)
    oauth_signature = marshmallow.fields.Str(required=True)
    oauth_signature_method = marshmallow.fields.Str(required=True)
    oauth_timestamp = marshmallow.fields.Str(required=True)
    oauth_version = marshmallow.fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)
        self._launch_verifier = request.find_service(name="launch_verifier")

    def lti_user(self):
        """
        Return an :class:`~lms.values.LTIUser` from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request

        :rtype: LTIUser
        """
        try:
            kwargs = parser.parse(self, self.context["request"], locations=["form"])
        except HTTPUnprocessableEntity as err:
            raise ValidationError(err.json) from err

        return LTIUser(
            kwargs["user_id"], kwargs["oauth_consumer_key"], kwargs.get("roles", "")
        )

    @marshmallow.validates_schema
    def _verify_oauth_1(self, _data):
        """
        Verify the request's OAuth 1 signature, timestamp, etc.

        :raise marshmallow.ValidationError: if the request doesn't have a valid
            OAuth 1 signature
        """
        try:
            self._launch_verifier.verify()
        except LTILaunchVerificationError as err:
            raise marshmallow.ValidationError("Invalid OAuth 1 signature.") from err
