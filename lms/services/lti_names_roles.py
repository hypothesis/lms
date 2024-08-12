"""
Service to talk to the Name and Roles LTIA API.

We only implement this now as a way to obtain the LTI Advantage Complete
certification and it's not used anywhere in the codebase yet.

https://www.imsglobal.org/spec/lti-nrps/v2p0
https://www.imsglobal.org/ltiadvantage
"""

from typing import TypedDict

from lms.models import LTIRegistration
from lms.services.ltia_http import LTIAHTTPService


class Member(TypedDict):
    """Structure of the members returned by the name and roles LTI API."""

    email: str
    family_name: str
    name: str
    picture: str
    roles: list[str]
    status: str
    user_id: str
    lti11_legacy_user_id: str | None


class LTINamesRolesService:
    LTIA_SCOPES = [
        "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
    ]

    def __init__(self, ltia_http_service: LTIAHTTPService):
        self._ltia_service = ltia_http_service

    def get_context_memberships(
        self, lti_registration: LTIRegistration, service_url: str
    ) -> list[Member]:
        """
        Get all the memberships of a context (a course).

        The course is defined by the service URL which will obtain
        from a LTI launch parameter and is always linked to an specific context.
        """
        response = self._ltia_service.request(
            lti_registration,
            "GET",
            service_url,
            scopes=self.LTIA_SCOPES,
            headers={
                "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
            },
        )

        return response.json()["members"]


def factory(_context, request):
    return LTINamesRolesService(ltia_http_service=request.find_service(LTIAHTTPService))
