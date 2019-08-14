from lms.services import HAPIError
from lms.values import HUser


__all__ = ["HypothesisOperationsService"]


class HypothesisOperationsService:
    """
    High-level h API service.

    The ``hapi`` service provides a low-level client for the Hypothesis "h"
    API. This service provides higher-level operations (eg. fetching a user)
    on top of that client.
    """

    def __init__(self, _context, request):
        self.hapi_svc = request.find_service(name="hapi")
        self.request = request

    def fetch_user(self, username):
        authority = self.request.registry.settings["h_authority"]
        userid = f"acct:{username}@{authority}"

        try:
            user_info = self.hapi_svc.get(path=f"users/{userid}").json()
            return HUser(
                authority=authority,
                username=username,
                display_name=user_info["display_name"],
            )
        except HAPIError as err:
            raise err
