from lms.services.ltia_http import LTIAHTTPService


class LTINamesRolesServices:
    LTIA_SCOPES = [
        "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
    ]

    def __init__(self, service_url, ltia_service: LTIAHTTPService):
        self._service_url = service_url
        self._ltia_service = ltia_service

    def context_memberships(self):
        response = self._ltia_service.request(
            "GET",
            self._service_url,
            scopes=self.LTIA_SCOPES,
            headers={
                "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
            },
        )
        from pprint import pprint

        pprint(response.json())


def factory(context, request):
    return LTINamesRolesServices(
        service_url=request.lti_jwt.get(
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice", {}
        ).get("context_memberships_url"),
        ltia_service=request.find_service(LTIAHTTPService),
    )
