from functools import wraps

from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from lms.services import HAPIError, HAPINotFoundError


def lti_h_action(function):
    """Disable an action if provisioning is not enabled and catch HAPIError."""

    @wraps(function)
    def wrapper(self, *args, **kwargs):
        # Pylint doesn't understand that self is "us" in this context
        if not self._context.provisioning_enabled:  # pylint: disable=protected-access
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

    def __init__(self, _context, request):
        self._context = request.context
        self._request = request

        self.h_api = request.find_service(name="h_api")
        self.group_info_service = request.find_service(name="group_info")

    @lti_h_action
    def add_user_to_group(self):
        """
        Add the Hypothesis user to the course group.

        Add the Hypothesis user corresponding to the current request's LTI
        user, to the Hypothesis group corresponding to the current request's
        LTI course.

        Assumes that the Hypothesis user and group have already been created.
        """

        self.h_api.add_user_to_group(
            h_user=self._context.h_user, group_id=self._context.h_groupid
        )

    @lti_h_action
    def upsert_h_user(self):
        """
        Create or update the Hypothesis user for the request's LTI user.

        Update the h user's information from LTI data. If the user doesn't
        exist yet, call the h API to create one.
        """

        self.h_api.upsert_user(
            h_user=self._context.h_user,
            provider=self._context.h_provider,
            provider_unique_id=self._context.h_provider_unique_id,
        )

    @lti_h_action
    def upsert_course_group(self):
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

        self._upsert_h_group(
            group_id=self._context.h_groupid,
            group_name=self._context.h_group_name,
            creator=self._context.h_user,
        )

        self.group_info_service.upsert(
            authority_provided_id=self._context.h_authority_provided_id,
            consumer_key=self._request.lti_user.oauth_consumer_key,
            params=self._request.params,
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
