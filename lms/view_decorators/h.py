# -*- coding: utf-8 -*-

"""View decorators for working with the h API."""

from __future__ import unicode_literals

import json
import requests

from pyramid.httpexceptions import HTTPBadGateway
from pyramid.httpexceptions import HTTPGatewayTimeout

from lms import util


def maybe_create_user(wrapped):
    """
    Create a user in h if one doesn't exist already.

    Call the h API to create a user for the authorized LTI user, if one doesn't
    exist already.
    """
    def wrapper(request, jwt):
        params = request.params

        # Only create users for application instances that we've enabled the
        # user integration feature for.
        oauth_consumer_key = params.get("oauth_consumer_key")
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

        # The user data that we will post to h.
        user_data = {
            "username": util.generate_username(params),
            "display_name": util.generate_display_name(params),
            "authority": authority,
            "identities": [
                {
                    "provider": util.generate_provider(params),
                    "provider_unique_id": util.generate_provider_unique_id(params),
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
