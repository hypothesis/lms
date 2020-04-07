from collections import namedtuple

from pyramid.httpexceptions import HTTPInternalServerError

from lms.services import HAPIError

Group = namedtuple("Group", "name groupid")


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

        self._h_api = request.find_service(name="h_api")
        self._group_info_service = request.find_service(name="group_info")

    def single_group_sync(self):
        """
        Sync standard data to H for an LTI launch.

        This will read a single group from the context object, upsert it, the
        current user and make that user a member of the group.
        """
        self.sync(
            groups=[
                Group(name=self._context.h_group_name, groupid=self._context.h_groupid)
            ]
        )

    def sync(self, groups):
        """
        Sync standard data to H for an LTI launch with the provided groups.

        This will upsert the provided list of groups, the current user and
        make that user a member of each group.

        :param groups: A list of Group objects.
        :raises HTTPInternalServerError: If we cannot sync to H for any reason
        """

        if not self._context.provisioning_enabled:  # pylint: disable=protected-access
            return None

        try:
            return self._sync_to_h(groups)

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    def _sync_to_h(self, groups):
        h_user = self._context.h_user

        self._h_api.upsert_user(
            h_user=h_user,
            provider=self._context.h_provider,
            provider_unique_id=self._context.h_provider_unique_id,
        )

        for group in groups:
            self._h_api.upsert_group(group_id=group.groupid, group_name=group.name)

            self._group_info_service.upsert(
                authority_provided_id=self._context.h_authority_provided_id,
                consumer_key=self._lti_user.oauth_consumer_key,
                params=self._request.params,
            )

        for group in groups:
            self._h_api.add_user_to_group(h_user=h_user, group_id=group.groupid)
