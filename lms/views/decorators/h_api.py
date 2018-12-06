# -*- coding: utf-8 -*-

"""View decorators for working with the h API."""

import functools

from pyramid.httpexceptions import HTTPBadRequest

from lms.services import HAPINotFoundError


def create_h_user(wrapped):  # noqa: MC0001
    """
    Update or create a Hypothesis LTI user.

    Update the h user's information from LTI data. If the user doesn't exist
    yet, call the h API to create one.

    Use this function as a decorator rather than calling it directly.
    The wrapped view must take ``request`` and ``jwt`` arguments::

      @view_config(...)
      @create_h_user
      def my_view(request, jwt):
          ...

    """
    # FIXME: This function doesn't do anything with the ``jwt`` argument,
    # other than pass it through to the wrapped view (or to the next decorator
    # on the wrapped view). The ``jwt`` argument has to be here because:
    #
    # - This decorator is called by the ``@lti_launch`` decorator (because
    #   ``@lti_launch`` is always placed above this decorator on decorated views)
    #   and ``@lti_launch`` passes a ``jwt_token`` argument when it calls this
    #   decorator.
    #
    # - The views that this decorator decorates expect a ``jwt`` argument so this
    #   decorator has to pass it to them (or rather it has to pass it down to the
    #   next decorator down in the stack, and it eventually gets passed to the
    #   view).
    #
    # This should all be refactored so that views and view decorators aren't
    # tightly coupled and arguments don't need to be passed through multiple
    # decorators to the view.
    def wrapper(request, jwt, context=None):
        context = context or request.context

        if not _auto_provisioning_feature_enabled(request):
            return wrapped(request, jwt)

        hapi_svc = request.find_service(name="hapi")

        # User data that is relevant to h
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

        # Send a PATCH user request to update user data to keep it in sync
        # with the data sent over LTI. This will succeed if the user already
        # exists.
        try:
            hapi_svc.patch(
                f"users/{context.h_username}", {"display_name": context.h_display_name}
            )
        except HAPINotFoundError:
            # Call the h API to create the user in h if it doesn't exist already.
            hapi_svc.post("users", user_data)

        return wrapped(request, jwt)

    return wrapper


def create_course_group(wrapped):
    """
    Create a Hypothesis group for the LTI course, if one doesn't exist already.

    Call the h API to create a group for the LTI course, if one doesn't exist
    already.

    Groups can only be created if the LTI user is allowed to create Hypothesis
    groups (for example instructors are allowed to create groups). If the group
    for the course hasn't been created yet, and if the user isn't allowed to
    create groups (e.g. if they're just a student) then show an error page
    instead of continuing with the LTI launch.

    Use this function as a view decorator rather than calling it directly.
    The decorated view must take ``request`` and ``jwt`` arguments::

      @view_config(...)
      @create_course_group
      def my_view(request, jwt):
          ...

    """
    # FIXME: This function doesn't do anything with the ``jwt`` argument,
    # other than pass it through to the wrapped view (or to the next decorator
    # on the wrapped view). The ``jwt`` argument has to be here because:
    #
    # - This decorator is called by the ``@lti_launch`` decorator (because
    #   ``@lti_launch`` is always placed above this decorator on decorated views)
    #   and ``@lti_launch`` passes a ``jwt_token`` argument when it calls this
    #   decorator.
    #
    # - The views that this decorator decorates expect a ``jwt`` argument so this
    #   decorator has to pass it to them (or rather it has to pass it down to the
    #   next decorator down in the stack, and it eventually gets passed to the
    #   view).
    #
    # This should all be refactored so that views and view decorators aren't
    # tightly coupled and arguments don't need to be passed through multiple
    # decorators to the view.
    def wrapper(request, jwt, context=None):
        _upsert_group(context or request.context, request)
        return wrapped(request, jwt)

    return wrapper


def add_user_to_group(wrapped):
    def wrapper(request, jwt, context=None):
        if not _auto_provisioning_feature_enabled(request):
            return wrapped(request, jwt)

        context = context or request.context

        request.find_service(name="hapi").post(
            f"groups/{context.h_groupid}/members/{context.h_userid}"
        )

        return wrapped(request, jwt)

    return wrapper


def _upsert_group(context, request):
    """Create or update the course group in h."""
    # Only create groups for application instances that we've enabled the
    # auto provisioning features for.
    if not _auto_provisioning_feature_enabled(request):
        return

    get_param = functools.partial(_get_param, request)

    hapi_svc = request.find_service(name="hapi")

    is_instructor = any(
        role in get_param("roles").lower()
        for role in ("administrator", "instructor", "teachingassisstant")
    )

    try:
        hapi_svc.patch(f"groups/{context.h_groupid}", {"name": context.h_group_name})
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


def _get_param(request, param_name):
    """Return the named param from the request or cause a 400."""
    try:
        return request.params[param_name]
    except KeyError:
        raise HTTPBadRequest(
            f'Required parameter "{param_name}" missing from LTI params'
        )


def _auto_provisioning_feature_enabled(request):
    oauth_consumer_key = _get_param(  # pylint: disable=too-many-function-args
        request, "oauth_consumer_key"
    )
    enabled_consumer_keys = request.registry.settings["auto_provisioning"]
    return oauth_consumer_key in enabled_consumer_keys
