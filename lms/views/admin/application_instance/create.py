from marshmallow import validate
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import IntegrityError
from webargs import fields

from lms.models.public_id import InvalidPublicId
from lms.security import Permissions
from lms.services import LTIRegistrationService
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class CreateAppInstanceSchema(PyramidRequestSchema):
    """Schema for creating a new application instance."""

    location = "form"

    developer_key = fields.Str(required=False, allow_none=True)
    developer_secret = fields.Str(required=False, allow_none=True)

    name = fields.Str(required=True, validate=validate.Length(min=1))
    lms_url = fields.URL(required=True)
    email = fields.Email(required=True)
    organization_public_id = fields.Str(required=True, validate=validate.Length(min=1))


class CreateAppInstanceSchemaV13(CreateAppInstanceSchema):
    """Schema for creating a new LTI 1.3 application instance."""

    deployment_id = fields.Str(required=True, validate=validate.Length(min=1))
    lti_registration_id = fields.Str(required=True)


@view_defaults(route_name="admin.instance.create", permission=Permissions.ADMIN)
class CreateApplicationInstanceViews(BaseApplicationInstanceView):
    def __init__(self, request):
        super().__init__(request)

        self.lti_registration_service: LTIRegistrationService = request.find_service(
            LTIRegistrationService
        )

    @view_config(
        request_method="GET",
        renderer="lms:templates/admin/application_instance/create.html.jinja2",
    )
    def create_start(self):
        """Show the page to kick off creating a new application instance."""

        lti_registration = None
        if lti_registration_id := self.request.params.get("lti_registration_id"):
            lti_registration = self.lti_registration_service.get_by_id(
                lti_registration_id.strip()
            )

        return dict(self.request.params, lti_registration=lti_registration)

    @view_config(request_method="POST")
    def create_callback(self):
        """Create an application instance (callback from the new AI page)."""

        lti_registration_id = self.request.params.get("lti_registration_id", "").strip()
        lti_registration_id = int(lti_registration_id) if lti_registration_id else None

        if flash_validation(
            self.request,
            CreateAppInstanceSchemaV13
            if lti_registration_id
            else CreateAppInstanceSchema,
        ):
            # Looks like something went wrong!
            return self._redirect("admin.instance.create", _query=self.request.params)

        try:
            ai = self.application_instance_service.create_application_instance(
                name=self.request.params["name"].strip(),
                lms_url=self.request.params["lms_url"].strip(),
                email=self.request.params["email"].strip(),
                deployment_id=self.request.params.get("deployment_id", "").strip(),
                developer_key=self.request.params.get("developer_key", "").strip(),
                developer_secret=self.request.params.get(
                    "developer_secret", ""
                ).strip(),
                organization_public_id=self.request.params.get(
                    "organization_public_id", ""
                ).strip(),
                lti_registration_id=lti_registration_id,
            )

        except InvalidPublicId as err:
            self.request.session.flash(
                {"organization_public_id": [str(err)]}, "validation"
            )

            return self._redirect("admin.instance.create", _query=self.request.params)

        except IntegrityError:
            self.request.session.flash(
                f"Application instance with deployment_id: {self.request.params['deployment_id']} already exists",
                "errors",
            )

            return self._redirect("admin.instance.create", _query=self.request.params)

        return self._redirect("admin.instance", id_=ai.id)
