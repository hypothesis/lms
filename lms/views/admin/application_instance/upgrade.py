from marshmallow import validate
from pyramid.httpexceptions import HTTPClientError
from pyramid.view import view_config, view_defaults
from sqlalchemy.exc import IntegrityError
from webargs import fields

from lms.security import Permissions
from lms.services import ApplicationInstanceNotFound, LTIRegistrationService
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin.application_instance._core import BaseApplicationInstanceView


class UpgradeApplicationInstanceSchema(PyramidRequestSchema):
    location = "form"

    consumer_key = fields.Str(required=True, validate=validate.Length(min=1))
    deployment_id = fields.Str(required=True, validate=validate.Length(min=1))


@view_defaults(permission=Permissions.ADMIN, route_name="admin.instance.upgrade")
class UpgradeApplicationInstanceViews(BaseApplicationInstanceView):
    def __init__(self, request) -> None:
        super().__init__(request)

        self.lti_registration_service: LTIRegistrationService = request.find_service(
            LTIRegistrationService
        )

    @view_config(
        request_method="GET",
        renderer="lms:templates/admin/application_instance/upgrade.html.jinja2",
    )
    def upgrade_instance_start(self):
        if lti_registration_id := self.request.params.get("lti_registration_id"):
            lti_registration = self.lti_registration_service.get_by_id(
                lti_registration_id.strip()
            )
        else:
            # This shouldn't really happen, but belt and braces
            raise HTTPClientError("`lti_registration_id` is required for an upgrade")

        return dict(self.request.params, lti_registration=lti_registration)

    @view_config(request_method="POST")
    def upgrade_instance_callback(self):
        if flash_validation(self.request, UpgradeApplicationInstanceSchema):
            return self._redirect("admin.instance.upgrade", _query=self.request.params)

        consumer_key = self.request.params["consumer_key"].strip()
        deployment_id = self.request.params["deployment_id"].strip()

        # Find the Application instance we are upgrading
        try:
            application_instance = (
                self.application_instance_service.get_by_consumer_key(consumer_key)
            )
        except ApplicationInstanceNotFound:
            self.request.session.flash(
                f"Can't find application instance: '{consumer_key}' for upgrade.",
                "errors",
            )

            return self._redirect("admin.instance.upgrade", _query=self.request.params)

        # Don't allow to change instances that already on 1.3
        if application_instance.lti_version == "1.3.0":
            self.request.session.flash(
                f"Application instance: '{consumer_key}' is already on LTI 1.3.",
                "errors",
            )

            return self._redirect("admin.instance.upgrade", _query=self.request.params)
        # Set the LTI1.3 values
        application_instance.lti_registration = self.lti_registration_service.get_by_id(
            self.request.params.get("lti_registration_id", "").strip()
        )
        application_instance.deployment_id = deployment_id
        try:
            # Flush here to find if we are making a duplicate in the process of
            # upgrading
            self.request.db.flush()

        except IntegrityError:
            # Leave a clean transaction, otherwise  we get a:
            #   "PendingRollbackError: This Session's transaction has been
            #   rolled back due to a previous exception during flush."
            self.request.db.rollback()

            self.request.session.flash(
                f"Application instance with deployment_id: {self.request.params['deployment_id']} already exists",
                "errors",
            )

            return self._redirect("admin.instance.upgrade", _query=self.request.params)

        return self._redirect("admin.instance", id_=application_instance.id)
