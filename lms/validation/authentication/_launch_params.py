"""Schema for validating LTI launch params."""

import marshmallow

from lms.models import LTIUser, display_name
from lms.services import LTILaunchVerificationError
from lms.validation._base import PyramidRequestSchema

__all__ = ("LaunchParamsAuthSchema",)


class LaunchParamsAuthSchema(PyramidRequestSchema):
    """
    Schema for LTI launch params.

    Validates and verifies LTI launch params. Usage via webargs::

        >>> from webargs.pyramidparser import parser
        >>>
        >>> schema = LaunchParamsAuthSchema(request)
        >>> parsed_params = parser.parse(schema, request, locations=["form"])

    Or to verify the request and get an models.LTIUser
    from the request's params::

        >>> schema = LaunchParamsAuthSchema(request)
        >>> schema.lti_user()
        LTIUser(user_id='...', ...)
    """

    user_id = marshmallow.fields.Str(required=True)
    roles = marshmallow.fields.Str(required=True)
    tool_consumer_instance_guid = marshmallow.fields.Str(required=True)
    lis_person_name_given = marshmallow.fields.Str(missing="")
    lis_person_name_family = marshmallow.fields.Str(missing="")
    lis_person_name_full = marshmallow.fields.Str(missing="")

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
        Return an models.LTIUser from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request

        :rtype: LTIUser
        """
        kwargs = self.parse(locations=["form"])

        return LTIUser(
            user_id=kwargs["user_id"],
            oauth_consumer_key=kwargs["oauth_consumer_key"],
            roles=kwargs["roles"],
            tool_consumer_instance_guid=kwargs["tool_consumer_instance_guid"],
            display_name=display_name(
                kwargs["lis_person_name_given"],
                kwargs["lis_person_name_family"],
                kwargs["lis_person_name_full"],
            ),
        )

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
