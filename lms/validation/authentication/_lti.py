import marshmallow

from lms.models import CLAIM_PREFIX, LTIUser
from lms.services.application_instance import ApplicationInstanceNotFound
from lms.services.launch_verifier import LTILaunchVerificationError
from lms.services.lti_user import LTIUserService
from lms.validation._exceptions import ValidationError
from lms.validation._lti_launch_params import LTIV11CoreSchema


class LTI11AuthSchema(LTIV11CoreSchema):
    """
    Schema for LTI launch params.

    Validates and verifies LTI launch params. Usage via webargs::

        >>> from webargs.pyramidparser import parser
        >>>
        >>> schema = LTI11AuthSchema(request)
        >>> parsed_params = parser.parse(schema, request, location="form")

    Or to verify the request and get an models.LTIUser
    from the request's params::

        >>> schema = LTI11AuthSchema(request)
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
        self._lti_user_service = request.find_service(LTIUserService)

    def lti_user(self) -> LTIUser:
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
            raise ValidationError(
                {"consumer_key": ["Invalid OAuth 1 signature. Unknown consumer key."]}
            ) from err

        return self._lti_user_service.from_lti_params(
            application_instance, self._request.lti_params
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
            raise marshmallow.ValidationError("Invalid OAuth 1 signature.") from err  # noqa: EM101, TRY003


class LTI13AuthSchema(LTIV11CoreSchema):
    """
    Schema used to validate the LTI1.3 params needed for authentication.

    Using the lti_user method produces an LTIUser based on those parameters.
    """

    location = "form"

    iss = marshmallow.fields.Str(required=True)
    aud = marshmallow.fields.Str(required=True)
    deployment_id = marshmallow.fields.Str(required=True)

    @marshmallow.pre_load
    def _lti_v13_fields(self, data, **_kwargs):
        if not self._request.lti_jwt:
            return data

        data["iss"] = data.v13.get("iss")
        data["aud"] = data.v13.get("aud")
        data["deployment_id"] = data.v13.get(f"{CLAIM_PREFIX}/deployment_id")

        return data

    def __init__(self, request):
        super().__init__(request)
        self._application_instance_service = request.find_service(
            name="application_instance"
        )
        self._lti_user_service = request.find_service(LTIUserService)

    def lti_user(self):
        """
        Return an models.LTIUser from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request
        """
        kwargs = self.parse(location="form")
        try:
            application_instance = (
                self._application_instance_service.get_by_deployment_id(
                    kwargs["iss"], kwargs["aud"], kwargs["deployment_id"]
                )
            )
        except ApplicationInstanceNotFound as err:
            raise ValidationError(
                {"JWT": ["Invalid LTI1.3 params. Unknown application_instance."]}
            ) from err

        return self._lti_user_service.from_lti_params(
            application_instance, self._request.lti_params
        )
