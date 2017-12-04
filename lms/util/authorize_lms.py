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
#   url = urllib.parse.urlparse(request.url)
#   url.params.append
    return request.url + "?state=" + state_guid

def authorize_lms(*args, client_id, client_secret, authorization_base_url,
        token_url, redirect_uri):
    def decorator(view_function):
        def wrapper(request, *args, user=None, **kwargs):
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

#
#client_id = "43460000000000123"
#client_secret = "TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOeLogm3sj0ESxCxlsxTSaDAObOK46XEZ84"
#authorization_base_url = 'https://atomicjolt.instructure.com/login/oauth2/auth'
#token_url = 'https://atomicjolt.instructure.com/login/oauth2/token'
#redirect_uri = 'https://8b608e88.ngrok.io/canvas_oauth_callback'
#
#import pyramid.httpexceptions as exc


#@view_config(route_name='canvas_oauth_callback', request_method='GET')
#def canvas_oauth_callback(request):
#
#  github = OAuth2Session(client_id, state=request.params['state'])
#  token = github.fetch_token(token_url, client_secret=client_secret,
#                             authorization_response=request.url, code=request.params['code'])
#
#@view_config(route_name='login', request_method='GET')
#def login(request):
#  oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
#  authorization_url, state = oauth_session.authorization_url(authorization_base_url)
#
#  raise exc.HTTPFound(authorization_url)
