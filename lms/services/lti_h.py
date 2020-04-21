from pyramid.httpexceptions import HTTPInternalServerError

from lms.services import HAPIError


class LTIHService:
    """
    Copy LTI users and courses to h users and groups.

    This service provides methods for synchronizing LTI users and courses (received by us in
    LTI launch parameters) to corresponding h users and groups. LTI users are copied to h
    by calling the h API to create corresponding h users, or to update the h users if they already
    exist. Similarly, LTI _courses_ are copied to h groups.

    All of these functions require you to be in an LTILaunchResource context.

    :raise HTTPInternalServerError: if any calls to the H API fail
    """

    def __init__(self, _context, request):
        self._context = request.context
        self._request = request
        self._lti_user = request.lti_user
        self._h_user = request.lti_user.h_user

        self._ai_getter = request.find_service(name="ai_getter")
        self._h_api = request.find_service(name="h_api")
        self._group_info_service = request.find_service(name="group_info")

    def single_group_sync(self):
        """
        Sync standard data to H for an LTI launch.

        This will read a single group from the context object, upsert it, the
        current user and make that user a member of the group.
        """
        self.sync(groups=[self._context.h_group])

    def sync(self, groups):
        """
        Sync standard data to H for an LTI launch with the provided groups.

        This will upsert the provided list of groups, the current user and
        make that user a member of each group.

        :param groups: A list of models.HGroup objects.
        :raises HTTPInternalServerError: If we cannot sync to H for any reason
        """

        if not self._ai_getter.provisioning_enabled():
            return None

        try:
            return self._sync_to_h(groups)

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    def _sync_to_h(self, groups):
        self._h_api.upsert_user(h_user=self._h_user)

        for group in groups:
            self._h_api.upsert_group(group)

            self._group_info_service.upsert(
                authority_provided_id=self._context.h_group.authority_provided_id,
                consumer_key=self._lti_user.oauth_consumer_key,
                params=self._request.params,
            )

        for group in groups:
            self._h_api.add_user_to_group(self._h_user, group)
