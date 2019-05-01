import functools
import urllib

import requests_oauthlib
import pyramid.httpexceptions as exc
from lms.models import find_or_create_from_user, find_user_from_state
from lms.models.tokens import build_token_from_oauth_response, update_user_token
from lms.util.jwt import build_jwt_from_lti_launch
from lms.util.lti import lti_params_for
from lms.services import ConsumerKeyError


def build_canvas_token_url(lms_url):
    """Build a canvas token url from the base lms url and the token."""
    return lms_url + "/login/oauth2/token"


def build_redirect_uri(request_url, redirect_endpoint):
    """Build a redirect uri back to the app."""
    req_url = urllib.parse.urlparse(request_url)
    return req_url.scheme + "://" + req_url.netloc + "/" + redirect_endpoint


def build_auth_base_url(lms_url, base_auth_endpoint):
    """Build base oauth url from lms_url and the provided base_auth_endpoint."""
    return lms_url + "/" + base_auth_endpoint


def default_oauth_condition(_request):
    """Determine whether or not we should make an oauth request."""
    return True


def authorize_lms(
    *,
    authorization_base_endpoint,
    redirect_endpoint,
    oauth_condition=default_oauth_condition
):
    """
    Decorate view function to support making an oauth request during an lti launch.

    Usage:
    @authorize_lms(
     # LMS oauth endpoint
     authorization_base_endpoint = 'login/oauth2/auth',

     # LMS token retrieval endpoint
     token_endpoint = 'login/oauth2/token',

     # Route where oauth response should be directed
     redirect_endpoint = 'canvas_oauth_callback',

     # Function to determine whether or not an oauth should be performed
     oauth_condition=lambda(request: True)
    )
    def my_route(request):
        ...
    """

    def decorator(view_function):
        """Decorate view function."""

        @functools.wraps(view_function)
        def wrapper(request, *args, user=None, **kwargs):
            """Redirect user."""
            if request.feature("new_oauth"):
                return view_function(request, *args, user=user, **kwargs)

            if oauth_condition(request) is False:
                return view_function(request, *args, user=user, **kwargs)

            ai_getter = request.find_service(name="ai_getter")
            consumer_key = request.params["oauth_consumer_key"]
            try:
                client_id = ai_getter.developer_key(consumer_key)
                lms_url = ai_getter.lms_url(consumer_key)
            except ConsumerKeyError:
                raise exc.HTTPInternalServerError()

            authorization_base_url = build_auth_base_url(
                lms_url, authorization_base_endpoint
            )

            redirect_uri = build_redirect_uri(request.url, redirect_endpoint)

            oauth_session = requests_oauthlib.OAuth2Session(
                client_id, redirect_uri=redirect_uri
            )
            authorization_url, state_guid = oauth_session.authorization_url(
                authorization_base_url
            )

            oauth_state = find_or_create_from_user(
                request.db, state_guid, user, request.params
            )
            if oauth_state is None:
                raise exc.HTTPInternalServerError()
            return exc.HTTPFound(location=authorization_url)

        return wrapper

    return decorator


def save_token(view_function):
    """Decorate an oauth callback route to save access token."""
    # pylint: disable=too-many-locals
    @functools.wraps(view_function)
    def wrapper(request, *args, **kwargs):
        """Route to handle content item selection oauth response."""
        if "state" not in request.params or "code" not in request.params:
            raise exc.HTTPInternalServerError("Invalid Oauth Response")

        lti_params = lti_params_for(request)

        ai_getter = request.find_service(name="ai_getter")
        consumer_key = lti_params["oauth_consumer_key"]
        try:
            client_id = ai_getter.developer_key(consumer_key)
            client_secret = ai_getter.developer_secret(consumer_key)
            lms_url = ai_getter.lms_url(consumer_key)
        except ConsumerKeyError:
            raise exc.HTTPInternalServerError()

        token_url = build_canvas_token_url(lms_url)

        state = request.params["state"]
        session = requests_oauthlib.OAuth2Session(client_id, state=state)
        oauth_resp = session.fetch_token(
            token_url,
            client_secret=client_secret,
            authorization_response=request.url,
            code=request.params["code"],
        )

        user = find_user_from_state(request.db, state)

        new_token = build_token_from_oauth_response(oauth_resp)
        update_user_token(request.db, new_token, user)
        jwt_token = build_jwt_from_lti_launch(
            lti_params, request.registry.settings["jwt_secret"]
        )

        return view_function(
            request,
            *args,
            token=new_token,
            lti_params=lti_params,
            user=user,
            jwt=jwt_token,
            **kwargs
        )

    return wrapper
