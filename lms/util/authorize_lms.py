from lms.config.settings import env_setting
from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
# TODO add as dependency
from requests_oauthlib import OAuth2Session
import pyramid.httpexceptions as exc
from lms.models.oauth_state import OauthState, find_by_state, is_valid_token, find_or_create_from_user
import urllib
import json

def build_oauth_done_url(request, state_guid):
    return request.url + "?state=" + state_guid

def authorize_lms(*args, authorization_base_url,
        token_url, redirect_uri):
    def decorator(view_function):
        def wrapper(request, *args, user=None, **kwargs):
            client_id = request.registry.settings['oauth.client_id']
            client_secret = request.registry.settings['oauth.client_secret']
            # TODO handle wrong params
            # TODO handle no user
            oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
            authorization_url, state_guid = oauth_session.authorization_url(authorization_base_url)
            token = find_by_state(request.db, state_guid)

            oauth_done_url = build_oauth_done_url(request, state_guid)
            lti_params = json.dumps(dict(request.params))
            oauth_state = find_or_create_from_user(request.db, state_guid,
                    user, oauth_done_url, lti_params)
            if(is_valid_token(token)):
                return view_function(request, *args, **kwargs)
            return HTTPFound(location=authorization_url)
        return wrapper
    return decorator
