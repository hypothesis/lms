from h_api.bulk_api import CommandBuilder


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
        self._lti_user = request.lti_user
        self._h_user = request.lti_user.h_user

        self._authority = request.registry.settings["h_authority"]
        self._application_instance_service = request.find_service(
            name="application_instance"
        )
        self._h_api = request.find_service(name="h_api")
        self._group_info_service = request.find_service(name="group_info")

    def sync(self, h_groups, group_info_params):
        """
        Sync standard data to h for an LTI launch with the provided groups.

        This will upsert the provided list of groups, the current user and
        make that user a member of each group.

        :param h_groups: the list of models.HGroup objects to upsert
        :param group_info_params: the params to record for these groups in
            models.GroupInfo

        :raise HTTPInternalServerError: if we can't sync to h for any reason
        :raise ApplicationInstanceNotFound: if request.lti_user.oauth_consumer_key isn't in the DB
        """

        if not self._application_instance_service.get().provisioning:
            return

        self._h_api.execute_bulk(commands=self._yield_commands(h_groups))

        # Keep a note of the groups locally for reporting purposes.
        for h_group in h_groups:
            self._group_info_service.upsert(
                h_group=h_group,
                consumer_key=self._lti_user.oauth_consumer_key,
                params=group_info_params,
            )

    def _yield_commands(self, h_groups):
        yield self._user_upsert(self._h_user)

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
