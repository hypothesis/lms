from h_api.bulk_api import CommandBuilder

from lms.models import Grouping
from lms.services import HAPI


class LTIHService:
    """
    Copy LTI users and courses to h users and groups.

    This service provides methods for synchronizing LTI users and courses (
    received by us in LTI launch parameters) to corresponding h users and
    groups using the Bulk API.

    All of these functions require you to be in an LTILaunchResource context.

    :raise HTTPInternalServerError: if any calls to the H API fail
    """

    def __init__(self, _context, request):
        self._h_user = request.lti_user.h_user
        self._application_instance = request.lti_user.application_instance

        self._authority = request.registry.settings["h_authority"]
        self._h_api: HAPI = request.find_service(HAPI)
        self._group_info_service = request.find_service(name="group_info")

    def sync(self, groupings: list[Grouping], group_info_params: dict):
        """
        Sync standard data to h for an LTI launch with the provided groups.

        This will upsert the provided list of groups, the current user and
        make that user a member of each group.

        :param groupings: groupings to sync to H
        :param group_info_params: params to add for each in `GroupInfo`

        :raise HTTPInternalServerError: if we can't sync to h for any reason
        :raise ApplicationInstanceNotFound: if
            `request.lti_user.oauth_consumer_key` isn't in the DB
        """
        self._h_api.execute_bulk(commands=self._yield_commands(groupings))

        # Keep a note of the groups locally for reporting purposes.
        for grouping in groupings:
            self._group_info_service.upsert_group_info(
                grouping=grouping, params=group_info_params
            )

    def _yield_commands(self, groupings):
        # Note! - Syncing a user to `h` currently has an implication for
        # reporting and so billing and will as long as our billing metric is
        # tied to users in groups. Should we start to sync users who have not
        # launched us, we could inflate our numbers or change their meaning.

        yield self._user_upsert(self._h_user)

        for i, grouping in enumerate(groupings):
            yield self._group_upsert(grouping, f"group_{i}")

        for i in range(len(groupings)):
            yield CommandBuilder.group_membership.create("user_0", f"group_{i}")

    def _user_upsert(self, h_user, ref="user_0"):
        return CommandBuilder.user.upsert(
            {
                "authority": self._authority,
                "username": h_user.username,
                "display_name": h_user.display_name,
                "identities": [
                    {
                        "provider": h_user.provider,
                        "provider_unique_id": h_user.provider_unique_id,
                    }
                ],
            },
            ref,
        )

    def _group_upsert(self, grouping, ref):
        return CommandBuilder.group.upsert(
            {
                "authority": self._authority,
                "name": grouping.name,
                "authority_provided_id": grouping.authority_provided_id,
            },
            ref,
        )
