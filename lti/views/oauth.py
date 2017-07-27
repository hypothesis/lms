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
    return oauth_callback(request, type_='token')


@view_config( route_name='refresh_callback' )
def refresh_callback(request):
    return oauth_callback(request, type='refresh')


def oauth_callback(request, type=None):
    """
    I'm not sure yet.
    
    Canvas called back with an authorization code. Use it to get or refresh an
    API token.
    
    """
    try:
        log.info ( 'oauth_callback: %s' % request.query_string )
        q = urlparse.parse_qs(request.query_string)
        code = q['code'][0]
        state = q['state'][0]
        dict = util.unpack_state(state)
        log.info ( 'oauth_callback: %s' % state)

        course = dict[constants.CUSTOM_CANVAS_COURSE_ID]
        user = dict[constants.CUSTOM_CANVAS_USER_ID]
        oauth_consumer_key = dict[constants.OAUTH_CONSUMER_KEY]
        ext_content_return_url = dict[constants.EXT_CONTENT_RETURN_URL]

        assignment_type = dict[constants.ASSIGNMENT_TYPE]
        assignment_name = dict[constants.ASSIGNMENT_NAME]
        assignment_value = dict[constants.ASSIGNMENT_VALUE]

        canvas_client_secret = request.auth_data.get_lti_secret(
            oauth_consumer_key)
        lti_refresh_token = request.auth_data.get_lti_refresh_token(
            oauth_consumer_key)
        canvas_server = request.auth_data.get_canvas_server(oauth_consumer_key)
        url = '%s/login/oauth2/token' % canvas_server
        grant_type = 'authorization_code' if type == 'token' else 'refresh_token'
        params = { 
                'grant_type': grant_type,
                'client_id': oauth_consumer_key,
                'client_secret': canvas_client_secret,
                'redirect_uri': '%s/token_init' % request.registry.settings['lti_server'] # this uri must match the uri in Developer Keys but is not called from
                }                                                                         # canvas. rather it calls token_callback or refresh callback
        if grant_type == 'authorization_code': 
            params['code'] = code
        else:
            params['refresh_token'] = lti_refresh_token
        r = requests.post(url, params)
        dict = r.json()
        lti_token = dict['access_token']
        if dict.has_key('refresh_token'): # does it ever not?
            lti_refresh_token = dict['refresh_token']
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
