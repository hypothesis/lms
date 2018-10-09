"""Oauth endpoint views."""
import jwt
from pyramid.view import view_config
from requests_oauthlib import OAuth2Session
from lms.models.tokens import update_user_token, build_token_from_oauth_response
from lms.models import find_user_from_state
from lms.util import lti_params_for
from lms.util.lti_launch import get_application_instance
from lms.views.content_item_selection import content_item_form


def build_canvas_token_url(lms_url):
    """Build a canvas token url from the base lms url and the token."""
    return lms_url + '/login/oauth2/token'


@view_config(route_name='canvas_oauth_callback', request_method='GET')
# pylint: disable=too-many-locals
def canvas_oauth_callback(request):
    """Route to handle content item selection oauth response."""
    state = request.params['state']

    lti_params = lti_params_for(request)
    consumer_key = lti_params['oauth_consumer_key']
    application_instance = get_application_instance(request.db, consumer_key)
    client_id = application_instance.developer_key

    aes_secret = request.registry.settings['aes_secret']
    client_secret = application_instance.decrypted_developer_secret(aes_secret)
    token_url = build_canvas_token_url(application_instance.lms_url)

    session = OAuth2Session(client_id, state=state)
    oauth_resp = session.fetch_token(token_url, client_secret=client_secret,
                                     authorization_response=request.url,
                                     code=request.params['code'])

    user = find_user_from_state(request.db, state)

    new_token = build_token_from_oauth_response(oauth_resp)
    update_user_token(request.db, new_token, user)
    data = {
        'user_id': lti_params['user_id'],
        'roles': lti_params['roles'],
        'consumer_key': consumer_key,
    }
    jwt_token = jwt.encode(data,
                           request.registry.settings['jwt_secret'],
                           'HS256').decode('utf-8')

    return content_item_form(
        request,
        lti_params=lti_params,
        lms_url=application_instance.lms_url,
        content_item_return_url=lti_params['content_item_return_url'],
        jwt=jwt_token
    )
