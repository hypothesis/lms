from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from lms.services import HAPIError, HAPINotFoundError


class LTIHypothesisBridge:
    @classmethod
    def add_user_to_group(cls, context, request):
        """
        Add the Hypothesis user to the course group.

        Add the Hypothesis user corresponding to the current request's LTI user, to
        the Hypothesis group corresponding to the current request's LTI course.

        Assumes that the Hypothesis user and group have already been created.

        Assumes that it's only used on LTI launch views.
        """

        if not context.provisioning_enabled:
            return

        try:
            request.find_service(name="h_api_requests").post(
                f"groups/{context.h_groupid}/members/{context.h_user.userid}"
            )
        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    @classmethod
    def upsert_h_user(cls, context, request):
        """
        Create or update the Hypothesis user for the request's LTI user.

        Update the h user's information from LTI data. If the user doesn't exist
        yet, call the h API to create one.

        Assumes that it's only used on LTI launch views.
        """
        if not context.provisioning_enabled:
            return

        hapi_svc = request.find_service(name="h_api_requests")

        user_data = {
            "username": context.h_user.username,
            "display_name": context.h_user.display_name,
            "authority": request.registry.settings["h_authority"],
            "identities": [
                {
                    "provider": context.h_provider,
                    "provider_unique_id": context.h_provider_unique_id,
                }
            ],
        }

        try:
            try:
                hapi_svc.patch(
                    f"users/{context.h_user.username}",
                    {"display_name": context.h_user.display_name},
                )
            except HAPINotFoundError:
                # Call the h API to create the user in h if it doesn't exist already.
                hapi_svc.post("users", user_data)

        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err

    @classmethod
    def upsert_course_group(cls, context, request):
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

        if not context.provisioning_enabled:
            return

        hapi_svc = request.find_service(name="h_api_requests")

        is_instructor = any(
            role in request.lti_user.roles.lower()
            for role in ("administrator", "instructor", "teachingassisstant")
        )

        try:
            try:
                hapi_svc.patch(
                    f"groups/{context.h_groupid}", {"name": context.h_group_name}
                )
            except HAPINotFoundError:
                # The group hasn't been created in h yet.
                if is_instructor:
                    # Try to create the group with the current instructor as its creator.
                    hapi_svc.put(
                        f"groups/{context.h_groupid}",
                        {"groupid": context.h_groupid, "name": context.h_group_name},
                        context.h_user.userid,
                    )
                else:
                    raise HTTPBadRequest("Instructor must launch assignment first.")
        except HAPIError as err:
            raise HTTPInternalServerError(explanation=err.explanation) from err
        else:
            cls._upsert_group_info(context, request)

    @classmethod
    def _upsert_group_info(cls, context, request):
        """Create or update the GroupInfo for the given request."""
        request.find_service(name="group_info_upsert")(
            context.h_authority_provided_id,
            request.lti_user.oauth_consumer_key,
            **{
                param: request.params.get(param)
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
