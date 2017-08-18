# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json

from pyramid.view import view_config

from lti import util
from lti.models import OAuth2UnvalidatedCredentials


@view_config(route_name='lti_credentials',
             renderer='lti:templates/lti_credentials_form.html.jinja2')
def lti_credentials(request):
    """
    Recieve credentials and save to database.

    Render the empty credentials form. When the form is submitted, save the unvalidated
    client id, client secret, authorization server and email address to the oauth2_unvalidated_credentials
    table and render the form and a thank you message confirming the submitted credentials.

    """
    credentials = util.requests.get_query_param(request, 'credentials')
    if credentials is None:
        return {
            'form_submitted': False
        }

    credentials = json.loads(credentials)

    request.db.add(OAuth2UnvalidatedCredentials(
        client_id=credentials.get("key"),
        client_secret=credentials.get("secret"),
        authorization_server=credentials.get("host"),
        email_address=credentials.get("email"),
    ))

    return {
        'form_submitted': True,
        'key': credentials.get("key"),
        'secret': credentials.get("secret"),
        'host': credentials.get("host"),
        'email': credentials.get("email"),
    }
