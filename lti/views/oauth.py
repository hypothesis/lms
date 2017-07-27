# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import urlparse
import traceback

import requests
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from lti import constants
from lti import util

log = logging.getLogger(__name__)


@view_config(route_name='token_callback')
def token_callback(request):
    """
    I'm not sure yet.

    This view gets called by Canvas when a Hypothesis assignment is launched
    _if_ we don't yet have an lti_token and lti_refresh_token for the developer
    key in canvas-auth.json yet. (So I think the first time, for a given developer
    key, that we're launched inside a Canvas assignment.)

    token_init() puts this view's URL in a request param that it sends to
    Canvas.

    """
    return oauth_callback(request, type_='token')


@view_config(route_name='refresh_callback')
def refresh_callback(request):
    """
    I'm not sure yet.

    This view gets called by Canvas when a Hypothesis assignment is launched
    _if_ the lti_token that we have in canvas-auth.json for the developer key
    is expired. refresh_init() puts this view's URL in a request param that it
    sends to Canvas.

    """
    return oauth_callback(request, type_='refresh')


def oauth_callback(request, type_=None):
    """
    I'm not sure yet.

    Canvas called back with an authorization code. Use it to get or refresh an
    API token.

    """
    try:
        log.info('oauth_callback: %s', request.query_string)
        parsed_query_string = urlparse.parse_qs(request.query_string)
        code = parsed_query_string['code'][0]
        state = parsed_query_string['state'][0]
        unpacked_state = util.unpack_state(state)
        log.info('oauth_callback: %s', state)

        course = unpacked_state[constants.CUSTOM_CANVAS_COURSE_ID]
        user = unpacked_state[constants.CUSTOM_CANVAS_USER_ID]
        oauth_consumer_key = unpacked_state[constants.OAUTH_CONSUMER_KEY]
        ext_content_return_url = unpacked_state[constants.EXT_CONTENT_RETURN_URL]

        assignment_type = unpacked_state[constants.ASSIGNMENT_TYPE]
        assignment_name = unpacked_state[constants.ASSIGNMENT_NAME]
        assignment_value = unpacked_state[constants.ASSIGNMENT_VALUE]

        canvas_client_secret = request.auth_data.get_lti_secret(
            oauth_consumer_key)
        lti_refresh_token = request.auth_data.get_lti_refresh_token(
            oauth_consumer_key)
        canvas_server = request.auth_data.get_canvas_server(oauth_consumer_key)
        url = '%s/login/oauth2/token' % canvas_server
        grant_type = 'authorization_code' if type_ == 'token' else 'refresh_token'
        params = {
            'grant_type': grant_type,
            'client_id': oauth_consumer_key,
            'client_secret': canvas_client_secret,
            'redirect_uri': '%s/token_init' % request.registry.settings['lti_server']  # this uri must match the uri in Developer Keys but is not called from
        }                                                                              # canvas. rather it calls token_callback or refresh callback
        if grant_type == 'authorization_code':
            params['code'] = code
        else:
            params['refresh_token'] = lti_refresh_token
        response = requests.post(url, params)
        unpacked_state = response.json()
        lti_token = unpacked_state['access_token']
        if 'refresh_token' in unpacked_state:  # Is it ever not?
            lti_refresh_token = unpacked_state['refresh_token']
        request.auth_data.set_tokens(oauth_consumer_key,
                                     lti_token,
                                     lti_refresh_token)
        return HTTPFound(location=request.route_url('lti_setup', _query={
            constants.CUSTOM_CANVAS_COURSE_ID: course,
            constants.CUSTOM_CANVAS_USER_ID: user,
            constants.OAUTH_CONSUMER_KEY: oauth_consumer_key,
            constants.EXT_CONTENT_RETURN_URL: ext_content_return_url,
            constants.ASSIGNMENT_TYPE: assignment_type,
            constants.ASSIGNMENT_NAME: assignment_name,
            constants.ASSIGNMENT_VALUE: assignment_value,
        }))
    except:
        response = traceback.print_exc()
        log.error(response)
        return util.simple_response(response)
