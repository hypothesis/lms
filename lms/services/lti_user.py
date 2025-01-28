from lms.models.lti_user import LTI, LTIUser, display_name
from lms.product.family import Family
from lms.services.application_instance import ApplicationInstanceService
from lms.services.lti_role_service import LTIRoleService


class LTIUserService:
    """
    A service to handle LTIUser.

    LTIUser is the center of many of our authentication schemas.
    This service handles de/serialization of LTIUsers.
    """

    def __init__(
        self,
        lti_role_service: LTIRoleService,
        application_instance_service: ApplicationInstanceService,
    ):
        self._lti_roles_service = lti_role_service
        self._application_instance_service = application_instance_service

    def from_lti_params(self, application_instance, lti_params) -> LTIUser:
        """Create an LTIUser from a LTIParams."""

        return self.deserialize(
            user_id=lti_params["user_id"],
            application_instance_id=application_instance.id,
            roles=lti_params["roles"],
            tool_consumer_instance_guid=lti_params["tool_consumer_instance_guid"],
            display_name=display_name(
                lti_params.get("lis_person_name_given", ""),
                lti_params.get("lis_person_name_family", ""),
                lti_params.get("lis_person_name_full", ""),
                lti_params.get("custom_display_name", ""),
            ),
            email=lti_params.get("lis_person_contact_email_primary"),
            lti={
                "course_id": lti_params.get("context_id"),
                "assignment_id": lti_params.get("resource_link_id"),
                "product_family": Family.from_launch(lti_params),
            },
        )

    @staticmethod
    def serialize(lti_user: LTIUser) -> dict:
        """
        Return a dict representing the LTIUser.

        LTIUser is often serialized. We can pick here the exact representation.
        """
        return {
            "user_id": lti_user.user_id,
            "roles": lti_user.roles,
            "tool_consumer_instance_guid": lti_user.tool_consumer_instance_guid,
            "display_name": lti_user.display_name,
            "application_instance_id": lti_user.application_instance_id,
            "email": lti_user.email,
            "lti": {
                "course_id": lti_user.lti.course_id,
                "assignment_id": lti_user.lti.assignment_id,
                "product_family": lti_user.lti.product_family,
            },
        }

    def deserialize(self, **kwargs: dict) -> LTIUser:
        """Create an LTIUser based on kwargs."""
        application_instance = self._application_instance_service.get_for_launch(
            kwargs["application_instance_id"]  # type: ignore  # noqa: PGH003
        )
        lti_roles = self._lti_roles_service.get_roles(str(kwargs["roles"]))
        effective_lti_roles = (
            self._lti_roles_service.get_roles_for_application_instance(
                application_instance, lti_roles
            )
        )
        lti_data = kwargs.pop("lti")
        lti = LTI(
            course_id=lti_data["course_id"],
            assignment_id=lti_data["assignment_id"],
            product_family=lti_data["product_family"],
        )

        return LTIUser(
            lti_roles=lti_roles,
            effective_lti_roles=effective_lti_roles,
            application_instance=application_instance,
            lti=lti,
            **kwargs,  # type: ignore  # noqa: PGH003
        )


def factory(_context, request):
    return LTIUserService(
        lti_role_service=request.find_service(LTIRoleService),
        application_instance_service=request.find_service(name="application_instance"),
    )
