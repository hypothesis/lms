from h_api.bulk_api import CommandBuilder
from pyramid.httpexceptions import HTTPInternalServerError

from lms.services import HAPIError


class LTIHService:  # pylint:disable=too-few-public-methods
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
        self._request = request
        self._lti_user = request.lti_user
        self._h_user = request.lti_user.h_user

        self._authority = request.registry.settings["h_authority"]
        self._ai_getter = request.find_service(name="ai_getter")
        self._h_api = request.find_service(name="h_api")
        self._group_info_service = request.find_service(name="group_info")

    def sync(self, h_groups):
        """
        Sync standard data to H for an LTI launch with the provided groups.

        This will upsert the provided list of groups, the current user and
        make that user a member of each group.

        :param h_groups: A list of models.HGroup objects.
        :raises HTTPInternalServerError: If we cannot sync to H for any reason
        """

        if not self._ai_getter.provisioning_enabled():
            return

        try:
            self._sync_to_h(h_groups)

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

        for h_group in h_groups:
            self._group_info_service.upsert(
                authority_provided_id=h_group.authority_provided_id,
                consumer_key=self._lti_user.oauth_consumer_key,
                params=self._request.params,
            )

    def _sync_to_h(self, h_groups):
        h_user = self._context.h_user

        if self._request.feature("use_serial_api"):
            self._h_api.upsert_user(h_user=h_user)

            for h_group in h_groups:
                self._h_api.upsert_group(h_group)

            for h_group in h_groups:
                self._h_api.add_user_to_group(h_user, h_group)

        else:
            self._h_api.bulk_action(
                commands=self._yield_commands(
                    h_user=self._context.h_user, h_groups=h_groups
                )
            )

    def _yield_commands(self, h_user, h_groups):
        yield self._user_upsert(h_user)

        for i, h_group in enumerate(h_groups):
            yield self._group_upsert(h_group, f"group_{i}")

        for i in range(len(h_groups)):
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

    def _group_upsert(self, h_group, ref):
        return CommandBuilder.group.upsert(
            {
                "authority": self._authority,
                "name": h_group.name,
                "authority_provided_id": h_group.authority_provided_id,
            },
            ref,
        )
