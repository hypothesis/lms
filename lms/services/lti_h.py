from h_api.bulk_api import CommandBuilder

from lms.models import Assignment, Grouping
from lms.services import HAPI


def checkpoint_sync_data(assignment: Assignment | None, lti_user) -> dict | None:
    """Build the checkpoint payload to sync to h for a Hide & Reveal assignment.

    Returns None when the assignment is missing or doesn't have checkpoint
    enabled, so callers can pass the result straight through to
    `LTIHService.sync(..., checkpoint_data=...)`.

    reveal_date is not sent — h is the source of truth for the reveal state.
    h's upsert uses coalesce to preserve an existing reveal_date when NULL
    is sent.
    """
    if not (assignment and assignment.checkpoint_enabled):
        return None

    role = "instructor" if lti_user.is_instructor else "student"
    return {
        "document_uri": assignment.document_url,
        "user": {
            "username": lti_user.h_user.username,
            "role": role,
        },
    }


class LTIHService:
    """
    Copy LTI users and courses to h users and groups.

    This service provides methods for synchronizing LTI users and courses (
    received by us in LTI launch parameters) to corresponding h users and
    groups using the Bulk API.

    All of these functions require you to be in an LTILaunchResource context.

    :raise HTTPInternalServerError: if any calls to the H API fail
    """

    def __init__(self, _context, request) -> None:
        self._h_user = request.lti_user.h_user
        self._application_instance = request.lti_user.application_instance

        self._authority = request.registry.settings["h_authority"]
        self._h_api: HAPI = request.find_service(HAPI)
        self._group_info_service = request.find_service(name="group_info")

    def sync(
        self,
        groupings: list[Grouping],
        group_info_params: dict,
        checkpoint_data: dict | None = None,
    ) -> list[dict] | None:
        """
        Sync standard data to h for an LTI launch with the provided groups.

        This will upsert the provided list of groups, the current user and
        make that user a member of each group.

        :param groupings: groupings to sync to H
        :param group_info_params: params to add for each in `GroupInfo`
        :param checkpoint_data: optional dict with document_uri and reveal_date
            to sync a checkpoint for each grouping
        :return: checkpoint results from h, or None

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

        if checkpoint_data:
            return self._sync_checkpoints(groupings, checkpoint_data)
        return None

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

    def _sync_checkpoints(
        self, groupings: list[Grouping], checkpoint_data: dict
    ) -> list[dict] | None:
        checkpoints = [
            {
                "group_authority_provided_id": grouping.authority_provided_id,
                "document_uri": checkpoint_data["document_uri"],
            }
            for grouping in groupings
        ]

        return self._h_api.sync_checkpoints(
            authority=self._authority,
            checkpoints=checkpoints,
            user=checkpoint_data.get("user"),
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
