"""Oauth endpoint views."""
import json
from pyramid.view import view_config
from requests_oauthlib import OAuth2Session
from lms.models.tokens import update_user_token, build_token_from_oauth_response
from lms.models.oauth_state import find_user_from_state, find_by_state
from lms.util.lti_launch import get_application_instance
from lms.views.content_item_selection import content_item_form
from lms.util.canvas_api import CanvasApi, GET


def build_canvas_token_url(lms_url):
    """Build a canvas token url from the base lms url and the token."""
    return lms_url + '/login/oauth2/token'


@view_config(route_name='canvas_oauth_callback', request_method='GET')
def canvas_oauth_callback(request):
    """Route to handle content item selection oauth response."""
    client_id = request.registry.settings['oauth.client_id']
    client_secret = request.registry.settings['oauth.client_secret']

    state = request.params['state']
    oauth_state = find_by_state(request.db, state)
    lti_params = json.loads(oauth_state.lti_params)
    consumer_key = lti_params['oauth_consumer_key']
    application_instance = get_application_instance(request.db, consumer_key)
    token_url = build_canvas_token_url(application_instance.lms_url)

    session = OAuth2Session(client_id, state=state)
    oauth_resp = session.fetch_token(token_url, client_secret=client_secret,
                                     authorization_response=request.url,
                                     code=request.params['code'])

    user = find_user_from_state(request.db, state)

    new_token = build_token_from_oauth_response(oauth_resp)
    update_user_token(request.db, new_token, user)

    return content_item_form(
        request,
        lti_params=lti_params,
        lms_url=application_instance.lms_url,
        content_item_return_url=lti_params['content_item_return_url'],
        jwt=None
    )
