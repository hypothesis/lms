from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from requests_oauthlib import OAuth2Session
from lms.models.tokens import update_user_token
from lms.models.oauth_state import find_user_from_state, find_by_state
from lms.util.lti_launch import get_application_instance
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer
from lms.models.oauth_state import find_by_state
from lms.views.content_item_selection import content_item_form
import json

authorization_base_url = 'https://atomicjolt.instructure.com/login/oauth2/auth'
token_url = 'https://atomicjolt.instructure.com/login/oauth2/token'

import pyramid.httpexceptions as exc

@view_config(route_name='canvas_oauth_callback', request_method='GET')
def canvas_oauth_callback(request):
  client_id = request.registry.settings['oauth.client_id']
  client_secret = request.registry.settings['oauth.client_secret']

  state = request.params['state']

 # TODO handle no state
  github = OAuth2Session(client_id, state=state)
  oauth_resp = github.fetch_token(token_url, client_secret=client_secret,
                             authorization_response=request.url, code=request.params['code'])
  oauth_state = find_by_state(request.db, state)
  user = find_user_from_state(request.db, state)

  token = update_user_token(request.db, oauth_resp, user)
#  return HTTPFound(location=oauth_state.auth_done_url)

  oauth_state = find_by_state(request.db, request.params['state'])
  lti_params = json.loads(oauth_state.lti_params)
  consumer_key = lti_params['oauth_consumer_key']
  application_instance = get_application_instance(request.db, consumer_key)
  #TODO remove old state
  return content_item_form(
      request,
      lti_params=lti_params,
      lms_url=application_instance.lms_url,
      content_item_return_url=lti_params['content_item_return_url'],
      jwt=None
  )
