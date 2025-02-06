"""
Service to talk to the Name and Roles LTIA API.

https://www.imsglobal.org/spec/lti-nrps/v2p0
https://www.imsglobal.org/ltiadvantage
"""

import logging
from typing import Any, TypedDict

from lms.models import LTIRegistration
from lms.services.ltia_http import LTIAHTTPService

LOG = logging.getLogger(__name__)


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
    message: list[dict]


class LTINamesRolesService:
    LTIA_SCOPES = [  # noqa: RUF012
        "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
    ]

    def __init__(self, ltia_http_service: LTIAHTTPService):
        self._ltia_service = ltia_http_service

    def get_context_memberships(
        self,
        lti_registration: LTIRegistration,
        service_url: str,
        resource_link_id: str | None = None,
        max_pages: int = 10,
        limit: int = 100,
    ) -> list[Member]:
        """
        Get the roster for a course or assignment.

        The course is defined by the service URL which will obtain
        from a LTI launch parameter and is always linked to an specific context.

        Optionally, using the  same service_url the API allows to get the roster of an assignment identified by `resource_link_id`.

        max_pages and limit control the default pagination limits.
        """

        query: dict[str, Any] = {"limit": limit}
        if resource_link_id:
            query["rlid"] = resource_link_id

        response = self._make_request(lti_registration, service_url, query)

        members = response.json()["members"]

        while response.links.get("next") and max_pages:
            LOG.info("Fetching next page of members %s", response.links["next"]["url"])
            response = self._make_request(
                lti_registration, response.links["next"]["url"], query
            )
            members.extend(response.json()["members"])

            max_pages -= 1

        return members

    def _make_request(self, lti_registration, service_url, query):
        return self._ltia_service.request(
            lti_registration,
            "GET",
            service_url,
            scopes=self.LTIA_SCOPES,
            headers={
                "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
            },
            params=query,
        )


def factory(_context, request):
    return LTINamesRolesService(ltia_http_service=request.find_service(LTIAHTTPService))
