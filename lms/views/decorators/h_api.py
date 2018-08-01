# -*- coding: utf-8 -*-

"""View decorators for working with the h API."""

from __future__ import unicode_literals

import json
import requests

from pyramid.httpexceptions import HTTPBadGateway
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPGatewayTimeout

from lms import util
from lms.util import MissingToolConsumerIntanceGUIDError
from lms.util import MissingUserIDError


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

        try:
            oauth_consumer_key = params["oauth_consumer_key"]
        except KeyError:
            raise HTTPBadRequest('Required parameter "oauth_consumer_key" missing from LTI params')

        # Only create users for application instances that we've enabled the
        # auto provisioning features for.
        enabled_consumer_keys = request.registry.settings["auto_provisioning"]
        if oauth_consumer_key not in enabled_consumer_keys:
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
