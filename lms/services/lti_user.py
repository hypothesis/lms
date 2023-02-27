from lms.models.lti_user import LTIUser, display_name
from lms.services import LTIRoleService


class LTIUserService:
    """
    A service to handle LTIUser.

    LTIUser is the center of many of our authentication schemas.
    This service handles de/serialization of LTIUsers.
    """

    def __init__(self, lti_role_service):
        self._lti_roles_service = lti_role_service

    def from_auth_params(self, application_instance, lti_core_schema) -> LTIUser:
        """Create an LTIUser from a LTIV11CoreSchema like dict."""

        return self.deserialize(
            user_id=lti_core_schema["user_id"],
            application_instance_id=application_instance.id,
            roles=lti_core_schema["roles"],
            tool_consumer_instance_guid=lti_core_schema["tool_consumer_instance_guid"],
            display_name=display_name(
                lti_core_schema["lis_person_name_given"],
                lti_core_schema["lis_person_name_family"],
                lti_core_schema["lis_person_name_full"],
            ),
            email=lti_core_schema["lis_person_contact_email_primary"],
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
        }

    def deserialize(self, **kwargs: dict) -> LTIUser:
        """Create an LTIUser based on kwargs."""
        lti_roles = self._lti_roles_service.get_roles(kwargs["roles"])

        return LTIUser(lti_roles=lti_roles, **kwargs)


def factory(_context, request):
    return LTIUserService(request.find_service(LTIRoleService))
