from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.validation import CanvasOAuthCallbackSchema


@view_config(
    route_name="canvas_api.authorize", request_method="GET", permission="canvas_api"
)
def authorize(request):
    ai_getter = request.find_service(name="ai_getter")
    consumer_key = request.lti_user.oauth_consumer_key

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
                    "state": CanvasOAuthCallbackSchema(request).state_param(),
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
    renderer="lms:templates/api/canvas/oauth2_redirect.html.jinja2",
    schema=CanvasOAuthCallbackSchema,
)
def oauth2_redirect(request):
    canvas_api_client = request.find_service(name="canvas_api_client")

    authorization_code = request.parsed_params["code"]

    token = canvas_api_client.get_token(authorization_code)
    canvas_api_client.save_token(*token)

    return {}
