import secrets
from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.validation import CanvasOAuthCallbackSchema


@view_config(
    route_name="canvas_api_authorize", request_method="GET", permission="canvas_api"
)
def authorize(request):
    ai_getter = request.find_service(name="ai_getter")
    consumer_key = request.lti_user.oauth_consumer_key

    state = request.session["canvas_api_authorize_state"] = secrets.token_hex()

    authorize_url = urlunparse(
        (
            "https",
            urlparse(ai_getter.lms_url(consumer_key)).netloc,
            "login/oauth2/auth",
            "",
            urlencode(
                {
                    "client_id": ai_getter.developer_key(consumer_key),
                    "response_type": "code",
                    "redirect_uri": request.route_url("canvas_oauth_callback"),
                    "state": state,
                }
            ),
            "",
        )
    )

    return HTTPFound(location=authorize_url)


@view_config(
    feature_flag="new_oauth",
    request_method="GET",
    route_name="canvas_oauth_callback",
    renderer="string",
    schema=CanvasOAuthCallbackSchema,
)
def oauth2_redirect(request):
    access_code = request.parsed_params["code"]
    state = request.parsed_params["state"]
    return f"""Redirect received
access_code: {access_code}
state: {state}"""
