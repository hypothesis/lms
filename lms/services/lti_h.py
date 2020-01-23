import hashlib
from functools import wraps

from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from lms.services import HAPIError, HAPINotFoundError
from lms.values import HUser


def lti_h_action(function):
    """Disable an action if provisioning is not enabled and catch HAPIError."""

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        # Pylint doesn't understand that self is "us" in this context
        if not self._provisioning_enabled:  # pylint: disable=protected-access
            return None

        try:
            return function(self, *args, **kwargs)

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    return wrapper


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

    DISPLAY_NAME_MAX_LENGTH = 30
    """The maximum length of an h display name."""

    GROUP_NAME_MAX_LENGTH = 25
    """The maximum length of an h group name."""
    
    USERNAME_MAX_LENGTH = 30
    """The maximum length of an h username."""

    def __init__(self, _context, request):
        self._context = request.context
        self._request = request

        self.h_api = request.find_service(name="h_api")
        self.group_info_service = request.find_service(name="group_info")
        self._ai_getter = request.find_service(name="ai_getter")

    @lti_h_action
    def add_user_to_groups(self):
        """
        Add the Hypothesis user to the course group.

        Add the Hypothesis user corresponding to the current request's LTI
        user, to the Hypothesis group corresponding to the current request's
        LTI course.

        Assumes that the Hypothesis user and group have already been created.
        """

        for groupid in self._h_groupids:
            self.h_api.add_user_to_groups(h_user=self._h_user, group_id=groupid)

    @lti_h_action
    def upsert_h_user(self):
        """
        Create or update the Hypothesis user for the request's LTI user.

        Update the h user's information from LTI data. If the user doesn't
        exist yet, call the h API to create one.
        """

        self.h_api.upsert_user(
            h_user=self._h_user,
            provider=self._h_provider,
            provider_unique_id=self._h_provider_unique_id,
        )

    @lti_h_action
    def upsert_course_groups(self):
        """
        Create or update the Hypothesis group for the request's LTI course.

        Call the h API to create a group for the LTI course, if one doesn't
        exist already.

        Groups can only be created if the LTI user is allowed to create
        Hypothesis groups (for example instructors are allowed to create
        groups).

        If the group for the course hasn't been created yet, and if the user
        isn't allowed to create groups (e.g. if they're just a student) then
        show an error page instead of continuing with the LTI launch.
        """

        for groupid, group_name in zip(self._h_groupids, self._h_group_names):
            self._upsert_h_group(
                group_id=groupid,
                group_name=group_name,
                creator=self._h_user,
            )

    def _upsert_h_group(self, group_id, group_name, creator):
        """Update the group and create it if the user is an instructor."""

        try:
            self.h_api.update_group(group_id=group_id, group_name=group_name)
            return

        except HAPINotFoundError:
            # The group hasn't been created in h yet.

            if not self._request.lti_user.is_instructor:
                raise HTTPBadRequest("Instructor must launch assignment first.")

        # Try to create the group with the current instructor as its creator.
        self.h_api.create_group(
            group_id=group_id, group_name=group_name, creator=creator
        )

    @property
    def _authority(self):
        return self._request.registry.settings["h_authority"]

    @property
    def _provisioning_enabled(self):
        """
        Return True if provisioning is enabled for this request.

        Return True if the provisioning feature is enabled for the current
        request, False otherwise.

        :raise HTTPBadRequest: if there's no oauth_consumer_key in the request
          params
        """
        return self._ai_getter.provisioning_enabled(
            self._request.lti_user.oauth_consumer_key
        )

    @property
    def _h_provider(self):
        """
        Return the h "provider" string for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          provider is missing
        """
        return self._request.json["tool_consumer_instance_guid"]

    @property
    def _h_provider_unique_id(self):
        """
        Return the h provider_unique_id for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          provider unique ID is missing
        """
        return self._request.lti_user.user_id

    @property
    def _h_user(self):
        return HUser(
            authority=self._authority,
            username=self._h_username,
            display_name=self._h_display_name,
        )

    @property
    def _h_username(self):
        """
        Return the h username for the current request.

        :raise HTTPBadRequest: if an LTI param needed for generating the
          username is missing
        """
        hash_object = hashlib.sha1()
        hash_object.update(self._h_provider.encode())
        hash_object.update(self._h_provider_unique_id.encode())
        return hash_object.hexdigest()[: self.USERNAME_MAX_LENGTH]
    @property
    def _h_display_name(self):
        """Return the h user display name for the current request."""
        full_name = (self._request.json.get("lis_person_name_full") or "").strip()
        given_name = (self._request.json.get("lis_person_name_given") or "").strip()
        family_name = (self._request.json.get("lis_person_name_family") or "").strip()

        if full_name:
            display_name = full_name
        else:
            display_name = " ".join((given_name, family_name))

        display_name = display_name.strip()

        display_name = display_name or "Anonymous"

        if len(display_name) > self.DISPLAY_NAME_MAX_LENGTH:
            display_name = (
                display_name[: self.DISPLAY_NAME_MAX_LENGTH - 1].rstrip() + "…"
            )

        return display_name

    @property
    def _h_groupids(self):
        return [f"group:{self._h_authority_provided_id}@{self._authority}"]

    @property
    def _h_group_names(self):
        name = self._request.json["context_title"].strip()

        if len(name) > self.GROUP_NAME_MAX_LENGTH:
            name = name[: self.GROUP_NAME_MAX_LENGTH - 1].rstrip() + "…"

        return [name]

    @property
    def _h_authority_provided_id(self):
        hash_object = hashlib.sha1()
        hash_object.update(self._request.json["tool_consumer_instance_guid"].encode())
        hash_object.update(self._request.json["context_id"].encode())
        return hash_object.hexdigest()
