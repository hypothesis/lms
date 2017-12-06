from lms.config.settings import env_setting
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
# TODO add as dependency
from requests_oauthlib import OAuth2Session
import pyramid.httpexceptions as exc
from lms.models.oauth_state import OauthState, find_by_state, find_or_create_from_user

from lms.models.application_instance import find_by_oauth_consumer_key

import urllib
import json

# authorization_base_url = 'https://atomicjolt.instructure.com/login/oauth2/auth',
# token_url = 'https://atomicjolt.instructure.com/login/oauth2/token',
# redirect_uri = 'https://localhost:8001/canvas_oauth_callback'

def build_canvas_redirect_uri(request_url, redirect_endpoint):
    req_url = urllib.parse.urlparse(request_url)
    return req_url.scheme+ "://" + req_url.netloc + "/" + redirect_endpoint

def build_canvas_authorization_base_url(lms_url, base_auth_endpoint):
    return lms_url + '/' + base_auth_endpoint
def build_canvas_token_url(lms_url, token_endpoint):
    return lms_url + '/' + token_endpoint
    

def build_oauth_done_url(request, state_guid):
    return request.url + "?state=" + state_guid

def authorize_lms(*args, authorization_base_endpoint,
        token_endpoint, redirect_endpoint):
    def decorator(view_function):
        def wrapper(request, *args, user=None, **kwargs):
            client_id = request.registry.settings['oauth.client_id']
            client_secret = request.registry.settings['oauth.client_secret']
            consumer_key = request.params['oauth_consumer_key']

            application_instance = find_by_oauth_consumer_key(request.db,
                    consumer_key)
            
            authorization_base_url = build_canvas_authorization_base_url(application_instance.lms_url,
                    authorization_base_endpoint)
            token_url = build_canvas_token_url(application_instance.lms_url,
                    token_endpoint)
            redirect_uri = build_canvas_redirect_uri(request.url,
                    redirect_endpoint)

            oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
            authorization_url, state_guid = oauth_session.authorization_url(authorization_base_url)
            token = find_by_state(request.db, state_guid)

            oauth_done_url = build_oauth_done_url(request, state_guid)
            lti_params = json.dumps(dict(request.params))
            oauth_state = find_or_create_from_user(request.db, state_guid,
                    user, oauth_done_url, lti_params)
            return HTTPFound(location=authorization_url)
        return wrapper
    return decorator
