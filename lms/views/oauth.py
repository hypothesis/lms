from pyramid.view import view_config
from requests_oauthlib import OAuth2Session
import os

client_id = "43460000000000123"
client_secret = "TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOeLogm3sj0ESxCxlsxTSaDAObOK46XEZ84"
authorization_base_url = 'https://atomicjolt.instructure.com/login/oauth2/auth'
token_url = 'https://atomicjolt.instructure.com/login/oauth2/token'
redirect_uri = 'https://d8a252a3.ngrok.io/canvas_oauth_callback'

import pyramid.httpexceptions as exc
# How can we persist user identity?
#  Maybe similar to oauth_state_middleware?
#  or add a state table?

# How can we keep track of token?
#  Token in the database? Associated with a user_id?

# How can we handle refreshing?
# Canvas Api Class?

## User
# id
# emails
# lms_id
# lms_provider
# lms_url

## Token
# access_token
# refresh_token
# expires_at
# user_id

## State
# user_id
# guid
# id

@view_config(route_name='canvas_oauth_callback', request_method='GET')
def canvas_oauth_callback(request):

  github = OAuth2Session(client_id, state=request.params['state'])
  token = github.fetch_token(token_url, client_secret=client_secret,
                             authorization_response=request.url, code=request.params['code'])
  raise exc.HTTPFound('https://google.com')

@view_config(route_name='login', request_method='GET')
def login(request):
  oauth_session = OAuth2Session(client_id, redirect_uri=redirect_uri)
  authorization_url, state = oauth_session.authorization_url(authorization_base_url)

  # State is used to prevent CSRF, keep this for later.
  raise exc.HTTPFound(authorization_url)




