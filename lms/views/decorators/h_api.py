# -*- coding: utf-8 -*-

"""View decorators for working with the h API."""

import functools
import json
import requests
from requests import RequestException

from pyramid.httpexceptions import HTTPBadRequest

from lms import models
from lms import util
from lms.views import HAPIError
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

        try:
            username = util.generate_username(params)
            provider = util.generate_provider(params)
            provider_unique_id = util.generate_provider_unique_id(params)
        except MissingToolConsumerIntanceGUIDError:
            raise HTTPBadRequest(
                'Required parameter "tool_consumer_instance_guid" missing from LTI params'
            )
        except MissingUserIDError:
            raise HTTPBadRequest('Required parameter "user_id" missing from LTI params')

        display_name = util.generate_display_name(params)

        # The user data that we will post to h.
        user_data = {
            "username": username,
            "display_name": display_name,
            "authority": request.registry.settings["h_authority"],
            "identities": [
                {"provider": provider, "provider_unique_id": provider_unique_id}
            ],
        }

        # Call the h API to create the user in h if it doesn't exist already.
        post(request.registry.settings, "/users", user_data, statuses=[409])

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
        if not _auto_provisioning_feature_enabled(request):
            return wrapped(request, jwt)

        get_param = functools.partial(_get_param, request)

        tool_consumer_instance_guid = get_param("tool_consumer_instance_guid")
        context_id = get_param("context_id")

        group = models.CourseGroup.get(
            request.db, tool_consumer_instance_guid, context_id
        )

        assert group is not None, (
            "create_course_group() should always have "
            "been run successfully before this "
            "function gets called, so group should "
            "never be None."
        )

        # Deliberately assume that generate_username() will succeed and not
        # raise an error.  create_h_user() should always have been run
        # successfully before this function gets called, so if
        # generate_username() was going to fail it would have already failed.
        username = util.generate_username(request.params)

        authority = request.registry.settings["h_authority"]
        userid = f"acct:{username}@{authority}"
        url = f"/groups/{group.pubid}/members/{userid}"

        post(request.registry.settings, url)

        return wrapped(request, jwt)

    return wrapper


def post(settings, path, data=None, username=None, statuses=None):
    """
    Do an H API post and return the response.

    If the request fails for any reason (for example a network connection error
    or a timeout) :exc:`~lms.views.HAPIError` is raised.
    :exc:`~lms.views.HAPIError` is also raised if a 4xx or 5xx response is
    received. Use the optional keyword argument ``statuses`` to supply a list
    of one or more 4xx or 5xx statuses for which :exc:`~lms.views.HAPIError`
    should not be raised -- the 4xx or 5xx response will be returned instead.

    :arg settings: the Pyramid request.registry.settings object
    :type settings: dict
    :arg path: the h API path to post to, relative to
      ``settings["h_api_url"]``, for example: ``"/users"`` or
      ``"/groups/<PUBID>/members/<USERID>"``
    :type path: str
    :arg data: the data to post as JSON in the request body
    :type data: dict
    :arg username: the username of the user to post as (using an
      X-Forwarded-User header)
    :type username: str
    :arg statuses: the list of 4xx and 5xx statuses that should not trigger an
      exception, for example: ``[409, 410]``
    :type statuses: list of ints

    :raise HAPIError: if the request fails for any reason, including if a 4xx
      or 5xx response is received

    :return: the response from the h API
    :rtype: requests.Response
    """
    statuses = statuses or []

    # Our OAuth 2.0 client_id and client_secret for authenticating to the h API.
    client_id = settings["h_client_id"]
    client_secret = settings["h_client_secret"]

    # The authority that we'll create h users and groups in.
    authority = settings["h_authority"]

    # The full h API URL to post to.
    url = settings["h_api_url"] + path

    post_args = dict(url=url, auth=(client_id, client_secret), timeout=1)

    if data is not None:
        post_args["data"] = json.dumps(data)

    if username is not None:
        post_args["headers"] = {
            "X-Forwarded-User": "acct:{username}@{authority}".format(
                username=username, authority=authority
            )
        }

    try:
        response = requests.post(**post_args)
        response.raise_for_status()
    except RequestException as err:
        response = getattr(err, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code is None or status_code not in statuses:
            raise HAPIError(
                explanation="Connecting to Hypothesis failed", response=response
            )

    return response


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
    if not any(
        role in get_param("roles").lower()
        for role in ("administrator", "instructor", "teachingassisstant")
    ):
        raise HTTPBadRequest("Instructor must launch assignment first.")

    # Generate the name for the new group.
    try:
        name = util.generate_group_name(request.params)
    except MissingContextTitleError:
        raise HTTPBadRequest(
            'Required parameter "context_title" missing from LTI params'
        )

    # Deliberately assume that generate_username() will succeed and not
    # raise an error.  create_h_user() should always have been run
    # successfully before this function gets called, so if
    # generate_username() was going to fail it would have already failed.
    username = util.generate_username(request.params)

    # Create the group in h.
    response = post(request.registry.settings, "/groups", {"name": name}, username)

    # Save a record of the group's pubid in the DB so that we can find it
    # again later.
    request.db.add(
        models.CourseGroup(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            context_id=context_id,
            pubid=response.json()["id"],
        )
    )


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
