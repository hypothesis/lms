from lms.values import HUser

__all__ = ["HAPIClient"]


class HAPIClient:
    """
    High-level h API service.

    This service supports high-level operations (eg. fetching a user) on h
    resources via the low-level "hapi" client.
    """

    def __init__(self, _context, request):
        self._h_api = request.find_service(name="h_api_requests")
        self._request = request

    def get_user(self, username):
        """
        Fetch an `HUser` given their username.

        :raise HAPIError: When the request to the h API fails for any reason
        :rtype: HUser
        """
        authority = self._request.registry.settings["h_authority"]
        userid = HUser(authority, username).userid

        # nb. Raises `HAPIError` if the request fails for any reason.
        user_info = self._h_api.get(path=f"users/{userid}").json()

        return HUser(
            authority=authority,
            username=username,
            display_name=user_info["display_name"],
        )
