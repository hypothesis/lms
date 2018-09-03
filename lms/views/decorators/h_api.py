# -*- coding: utf-8 -*-

"""View decorators for working with the h API."""

from __future__ import unicode_literals

import functools
import json
import requests

from pyramid.httpexceptions import HTTPBadGateway
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPGatewayTimeout

from lms import models
from lms import util
from lms.util import MissingToolConsumerIntanceGUIDError
from lms.util import MissingUserIDError
from lms.util import MissingContextTitleError


def create_h_user(wrapped):  # noqa: MC0001
    """
    Create a user in h if one doesn't exist already.

    Call the h API to create a user for the authorized LTI user, if one doesn't
    exist already.

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
    def wrapper(request, jwt):  # pylint: disable=too-many-branches
        params = request.params

        if not _auto_provisioning_feature_enabled(request):
            return wrapped(request, jwt)

        # Our OAuth 2.0 client_id and client_secret for authenticating to the h API.
        client_id = request.registry.settings["h_client_id"]
        client_secret = request.registry.settings["h_client_secret"]

        # The authority that we'll create h users and groups in.
        authority = request.registry.settings["h_authority"]

        # The URL of h's create user API endpoint.
        create_user_api_url = request.registry.settings["h_api_url"] + "/users"

        try:
            username = util.generate_username(params)
            provider = util.generate_provider(params)
            provider_unique_id = util.generate_provider_unique_id(params)
        except MissingToolConsumerIntanceGUIDError:
            raise HTTPBadRequest('Required parameter "tool_consumer_instance_guid" missing from LTI params')
        except MissingUserIDError:
            raise HTTPBadRequest('Required parameter "user_id" missing from LTI params')

        display_name = util.generate_display_name(params)

        # The user data that we will post to h.
        user_data = {
            "username": username,
            "display_name": display_name,
            "authority": authority,
            "identities": [
                {
                    "provider": provider,
                    "provider_unique_id": provider_unique_id,
                }
            ],
        }

        # Call the h API to create the user in h if it doesn't exist already.
        try:
            response = requests.post(
                create_user_api_url,
                auth=(client_id, client_secret),
                data=json.dumps(user_data),
                timeout=1,
            )
        except requests.exceptions.ReadTimeout:
            raise HTTPGatewayTimeout(explanation="Connecting to Hypothesis failed")

        if response.status_code == 200:
            # User was created successfully.
            pass
        elif response.status_code == 409:
            # The user already exists in h, so we don't need to do anything.
            pass
        else:
            # Something unexpected went wrong when trying to create the user
            # account in h. Abort and show the user an error page.
            raise HTTPBadGateway(explanation="Connecting to Hypothesis failed")

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
    def wrapper(request, jwt):
        _maybe_create_group(request)
        return wrapped(request, jwt)
    return wrapper


def add_user_to_group(wrapped):
    def wrapper(request, jwt):
        get_param = functools.partial(_get_param, request)

        tool_consumer_instance_guid = get_param("tool_consumer_instance_guid")
        context_id = get_param("context_id")

        group = models.CourseGroup.get(request.db, tool_consumer_instance_guid, context_id)
        username = util.generate_username(request.params)
        authority = request.registry.settings["h_authority"]
        userid = f"acct:{username}@{authority}"
        client_id = request.registry.settings["h_client_id"]
        client_secret = request.registry.settings["h_client_secret"]

        response = requests.post(
            request.registry.settings["h_api_url"] + f"/groups/{group.pubid}/members/{userid}",
            auth=(client_id, client_secret),
            headers={
                "X-Forwarded-User": userid,
            },
            timeout=1,
        )

        return wrapped(request, jwt)
    return wrapper


def _maybe_create_group(request):
    """Create a Hypothesis group for the LTI course, if one doesn't exist."""
    # Only create groups for application instances that we've enabled the
    # auto provisioning features for.
    if not _auto_provisioning_feature_enabled(request):
        return

    get_param = functools.partial(_get_param, request)

    tool_consumer_instance_guid = get_param("tool_consumer_instance_guid")
    context_id = get_param("context_id")

    group = models.CourseGroup.get(request.db, tool_consumer_instance_guid, context_id)

    if group:
        # The group has already been created in h, nothing more to do here.
        return

    # Show the user an error page if the group hasn't been created yet and
    # the user isn't allowed to create groups.
    if not any(role in get_param("roles").lower() for role in ("administrator", "instructor", "teachingassisstant")):
        raise HTTPBadRequest("Instructor must launch assignment first.")

    create_group_api_url = request.registry.settings["h_api_url"] + "/groups"
    client_id = request.registry.settings["h_client_id"]
    client_secret = request.registry.settings["h_client_secret"]

    # Generate the name for the new group.
    try:
        name = util.generate_group_name(request.params)
    except MissingContextTitleError:
        raise HTTPBadRequest('Required parameter "context_title" missing from LTI params')

    authority = request.registry.settings["h_authority"]
    username = util.generate_username(request.params)

    # Create the group in h.
    try:
        response = requests.post(
            create_group_api_url,
            auth=(client_id, client_secret),
            data=json.dumps({"name": name}),
            headers={
                "X-Forwarded-User": "acct:{username}@{authority}".format(username=username, authority=authority),
            },
            timeout=1,
        )
        response.raise_for_status()
    except requests.RequestException:
        raise HTTPGatewayTimeout(explanation="Connecting to Hypothesis failed")

    # Save a record of the group's pubid in the DB so that we can find it
    # again later.
    request.db.add(models.CourseGroup(
        tool_consumer_instance_guid=tool_consumer_instance_guid,
        context_id=context_id,
        pubid=response.json()["id"],
    ))


def _get_param(request, param_name):
    """Return the named param from the request or cause a 400."""
    try:
        return request.params[param_name]
    except KeyError:
        raise HTTPBadRequest(f'Required parameter "{param_name}" missing from LTI params')


def _auto_provisioning_feature_enabled(request):
    oauth_consumer_key = _get_param(request, "oauth_consumer_key")
    enabled_consumer_keys = request.registry.settings["auto_provisioning"]
    return oauth_consumer_key in enabled_consumer_keys
