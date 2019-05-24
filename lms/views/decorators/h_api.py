"""View decorators for working with the h API."""

import functools

from pyramid.httpexceptions import HTTPBadRequest

from lms.services import HAPINotFoundError


__all__ = ["upsert_h_user", "upsert_course_group", "add_user_to_group"]


def upsert_h_user(wrapped):
    """
    Create or update the Hypothesis user for the request's LTI user.

    Update the h user's information from LTI data. If the user doesn't exist
    yet, call the h API to create one.

    Assumes that it's only used on LTI launch views.
    """

    @functools.wraps(wrapped)
    def wrapper(context, request):
        if not context.provisioning_enabled:
            return wrapped(context, request)

        hapi_svc = request.find_service(name="hapi")

        user_data = {
            "username": context.h_username,
            "display_name": context.h_display_name,
            "authority": request.registry.settings["h_authority"],
            "identities": [
                {
                    "provider": context.h_provider,
                    "provider_unique_id": context.h_provider_unique_id,
                }
            ],
        }

        try:
            hapi_svc.patch(
                f"users/{context.h_username}", {"display_name": context.h_display_name}
            )
        except HAPINotFoundError:
            # Call the h API to create the user in h if it doesn't exist already.
            hapi_svc.post("users", user_data)

        return wrapped(context, request)

    return wrapper


def upsert_course_group(wrapped):
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

    @functools.wraps(wrapped)
    def wrapper(context, request):
        if not context.provisioning_enabled:
            return wrapped(context, request)

        hapi_svc = request.find_service(name="hapi")

        is_instructor = any(
            role in request.params["roles"].lower()
            for role in ("administrator", "instructor", "teachingassisstant")
        )

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
                    context.h_userid,
                )
            else:
                raise HTTPBadRequest("Instructor must launch assignment first.")
        return wrapped(context, request)

    return wrapper


def add_user_to_group(wrapped):
    """
    Add the Hypothesis user to the course group.

    Add the Hypothesis user corresponding to the current request's LTI user, to
    the Hypothesis group corresponding to the current request's LTI course.

    Assumes that the Hypothesis user and group have already been created.

    Assumes that it's only used on LTI launch views.
    """

    @functools.wraps(wrapped)
    def wrapper(context, request):
        if not context.provisioning_enabled:
            return wrapped(context, request)

        request.find_service(name="hapi").post(
            f"groups/{context.h_groupid}/members/{context.h_userid}"
        )

        return wrapped(context, request)

    return wrapper
