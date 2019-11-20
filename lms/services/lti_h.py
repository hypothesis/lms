from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from lms.services import HAPIError, HAPINotFoundError


class LTIHService:
    """Actions which import import data from LTI to H."""

    def __init__(self, _context, request):
        self._context = request.context
        self._request = request

        self.h_api = request.find_service(name="h_api")
        self.group_info_upsert_service = request.find_service(name="group_info_upsert")

    def add_user_to_group(self):
        """
        Add the Hypothesis user to the course group.

        Add the Hypothesis user corresponding to the current request's LTI user, to
        the Hypothesis group corresponding to the current request's LTI course.

        Assumes that the Hypothesis user and group have already been created.

        Assumes that it's only used on LTI launch views.
        """

        if not self._context.provisioning_enabled:
            return

        try:
            self.h_api.add_user_to_group(
                h_user=self._context.h_user, group_id=self._context.h_groupid
            )
        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    def upsert_h_user(self):
        """
        Create or update the Hypothesis user for the request's LTI user.

        Update the h user's information from LTI data. If the user doesn't exist
        yet, call the h API to create one.

        Assumes that it's only used on LTI launch views.
        """
        if not self._context.provisioning_enabled:
            return

        try:
            self.h_api.upsert_user(
                h_user=self._context.h_user,
                provider=self._context.h_provider,
                provider_unique_id=self._context.h_provider_unique_id,
            )

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    def upsert_course_group(self):
        """
        Create or update the Hypothesis group for the request's LTI course.

        Call the h API to create a group for the LTI course, if one doesn't exist
        already.

        Groups can only be created if the LTI user is allowed to create Hypothesis
        groups (for example instructors are allowed to create groups). If the group
        for the course hasn't been created yet, and if the user isn't allowed to
        create groups (e.g. if they're just a student) then show an error page
        instead of continuing with the LTI launch.

        Assumes that it's only used on LTI launch views.
        """

        if not self._context.provisioning_enabled:
            return

        try:
            try:
                self.h_api.update_group(
                    group_id=self._context.h_groupid,
                    group_name=self._context.h_group_name,
                )

            except HAPINotFoundError:
                # The group hasn't been created in h yet.

                if not self._is_instructor(self._request.lti_user):
                    raise HTTPBadRequest("Instructor must launch assignment first.")

                # Try to create the group with the current instructor as its creator.
                self.h_api.create_group(
                    group_id=self._context.h_groupid,
                    group_name=self._context.h_group_name,
                    h_user=self._context.h_user,
                )

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err
        else:
            self._upsert_group_info()

    @classmethod
    def _is_instructor(cls, lti_user):
        return any(
            role in lti_user.roles.lower()
            for role in ("administrator", "instructor", "teachingassisstant")
        )

    def _upsert_group_info(self):
        """Create or update the GroupInfo for the given request."""

        self.group_info_upsert_service(
            self._context.h_authority_provided_id,
            self._request.lti_user.oauth_consumer_key,
            **{
                param: self._request.params.get(param)
                for param in [
                    "context_id",
                    "context_title",
                    "context_label",
                    "tool_consumer_info_product_family_code",
                    "tool_consumer_info_version",
                    "tool_consumer_instance_name",
                    "tool_consumer_instance_description",
                    "tool_consumer_instance_url",
                    "tool_consumer_instance_contact_email",
                    "tool_consumer_instance_guid",
                    "custom_canvas_api_domain",
                    "custom_canvas_course_id",
                ]
            },
        )
