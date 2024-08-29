"""
Service to talk to the Name and Roles LTIA API.

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
        self,
        lti_registration: LTIRegistration,
        service_url: str,
        resource_link_id: str | None = None,
    ) -> list[Member]:
        """
        Get the roster for a course or assignment.

        The course is defined by the service URL which will obtain
        from a LTI launch parameter and is always linked to an specific context.

        Optically, using the  same service_url the API allows to get the roster of an assignment identified by `resource_link_id`.
        """
        query = {}
        if resource_link_id:
            query["rlid"] = resource_link_id

        response = self._ltia_service.request(
            lti_registration,
            "GET",
            service_url,
            scopes=self.LTIA_SCOPES,
            headers={
                "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
            },
            params=query,
        )

        return response.json()["members"]


def factory(_context, request):
    return LTINamesRolesService(ltia_http_service=request.find_service(LTIAHTTPService))
