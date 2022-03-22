"""Schema for validating LTI launch params."""

import marshmallow

from lms.models import LTIUser
from lms.services import ApplicationInstanceNotFound, LTILaunchVerificationError
from lms.validation._base import PyramidRequestSchema
from lms.validation._lti import LTIAuthParamsSchema

__all__ = ("LaunchParamsAuthSchema",)


class LaunchParamsAuthSchema(LTIAuthParamsSchema, PyramidRequestSchema):
    """
    Schema for LTI launch params.

    Validates and verifies LTI launch params. Usage via webargs::

        >>> from webargs.pyramidparser import parser
        >>>
        >>> schema = LaunchParamsAuthSchema(request)
        >>> parsed_params = parser.parse(schema, request, location="form")

    Or to verify the request and get an models.LTIUser
    from the request's params::

        >>> schema = LaunchParamsAuthSchema(request)
        >>> schema.lti_user()
        LTIUser(user_id='...', ...)
    """

    oauth_consumer_key = marshmallow.fields.Str(required=True)
    oauth_nonce = marshmallow.fields.Str(required=True)
    oauth_signature = marshmallow.fields.Str(required=True)
    oauth_signature_method = marshmallow.fields.Str(required=True)
    oauth_timestamp = marshmallow.fields.Str(required=True)
    oauth_version = marshmallow.fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)
        self._launch_verifier = request.find_service(name="launch_verifier")
        self._application_instance_service = request.find_service(
            name="application_instance"
        )

    def lti_user(self):
        """
        Return a models.LTIUser from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request

        :rtype: LTIUser
        """
        kwargs = self.parse(location="form")

        try:
            application_instance = (
                self._application_instance_service.get_by_consumer_key(
                    kwargs["oauth_consumer_key"]
                )
            )
        except ApplicationInstanceNotFound as err:
            raise marshmallow.ValidationError(
                "Invalid OAuth 1 signature. Unknown consumer key."
            ) from err

        return LTIUser.from_auth_params(application_instance, kwargs)

    @marshmallow.validates_schema
    def _verify_oauth_1(self, _data, **_kwargs):
        """
        Verify the request's OAuth 1 signature, timestamp, etc.

        :raise marshmallow.ValidationError: if the request doesn't have a valid
            OAuth 1 signature
        """
        try:
            self._launch_verifier.verify()
        except LTILaunchVerificationError as err:
            raise marshmallow.ValidationError("Invalid OAuth 1 signature.") from err
