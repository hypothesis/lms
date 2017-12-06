"""
Decorator to support making an oauth request to an lms during an lti launch

Usage:
@authorize_lms(
 authorization_base_endpoint = 'login/oauth2/auth', # LMS oauth endpoint
 token_endpoint = 'login/oauth2/token', # LMS token retrieval endpoint
 redirect_endpoint = 'canvas_oauth_callback' # Route where oauth response
 should be directed
)
def my_route(request):
    ...
"""
import urllib
# import json

from pyramid.httpexceptions import HTTPFound
from requests_oauthlib import OAuth2Session
# from lms.models.oauth_state import find_by_state, find_or_create_from_user
from lms.models.application_instance import find_by_oauth_consumer_key

def build_redirect_uri(request_url, redirect_endpoint):
    """
    Build redirect uri from the current request uri and the provided
    redirect endpoint
    """
    req_url = urllib.parse.urlparse(request_url)
    return req_url.scheme+ "://" + req_url.netloc + "/" + redirect_endpoint

def build_auth_base_url(lms_url, base_auth_endpoint):
    """Build base oauth url from lms_url and the provided base_auth_endpoint"""
    return lms_url + '/' + base_auth_endpoint

def authorize_lms(*, authorization_base_endpoint, redirect_endpoint):
    """
    Initialize decorator to redirect user to LMS for oauth, while saving
    application state to be used upon oauth response
    """
    def decorator():
        """
        Decorate view function
        """
        def wrapper(request, *, _user=None):
            """
            Redirect user
            """
            client_id = request.registry.settings['oauth.client_id']
            consumer_key = request.params['oauth_consumer_key']

            application_instance = find_by_oauth_consumer_key(request.db, consumer_key)

            authorization_base_url = build_auth_base_url(application_instance.lms_url,
                                                         authorization_base_endpoint)

            redirect_uri = build_redirect_uri(request.url, redirect_endpoint)

            oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
            authorization_url, _state_guid = oauth_session.authorization_url(authorization_base_url)

            # TODO - we should be able to check the token to see if it is
            # still valid, if so we should not oauth again
            # token = find_by_state(request.db, state_guid)
            # lti_params = json.dumps(dict(request.params))
            # oauth_state = find_or_create_from_user(request.db, state_guid,
            #        user, lti_params)
            return HTTPFound(location=authorization_url)
        return wrapper
    return decorator
