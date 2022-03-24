import marshmallow

from lms.models import LTIUser
from lms.services import ApplicationInstanceNotFound
from lms.validation._base import PyramidRequestSchema
from lms.validation._exceptions import ValidationError
from lms.validation._lti import LTIAuthParamsSchema


class LTI13AuthSchema(LTIAuthParamsSchema, PyramidRequestSchema):
    """
    Schema used to validate the LTI1.3 params needed for authentication.

    Using the lti_user method produces an LTIUser based on those parameters.
    """

    location = "form"

    issuer = marshmallow.fields.Str(required=True)
    client_id = marshmallow.fields.Str(required=True)
    deployment_id = marshmallow.fields.Str(required=True)

    def __init__(self, request):
        super().__init__(request)
        self._application_instance_service = request.find_service(
            name="application_instance"
        )

    def lti_user(self):
        """
        Return an models.LTIUser from the request's launch params.

        :raise ValidationError: if the request isn't a valid LTI launch request
        """
        kwargs = self.parse(location="form")
        try:
            application_instance = (
                self._application_instance_service.get_by_deployment_id(
                    kwargs["issuer"], kwargs["client_id"], kwargs["deployment_id"]
                )
            )
        except ApplicationInstanceNotFound as err:
            raise ValidationError(
                "Invalid LTI1.3 params. Unknown application_instance."
            ) from err

        return LTIUser.from_auth_params(application_instance, kwargs)
