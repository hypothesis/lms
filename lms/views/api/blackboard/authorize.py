from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(
    request_method="GET", route_name="blackboard_api.authorize", permission="blackboard_api"
)
def authorize(request):
    ai_getter = request.find_service(name="ai_getter")

    client_id = "8baa49c0-fb04-4404-acca-7b9bb51405e0"

    authorize_url = urlunparse(
        (
            "https",
            urlparse(ai_getter.lms_url()).netloc,
            #"api/v1/gateway/oauth2/jwttoken",
            "learn/api/public/v1/oauth2/authorizationcode",
            "",
            urlencode(
                {
                    "client_id": client_id,
                    "response_type": "code",
                    "redirect_uri": request.route_url("blackboard_oauth_callback"),
                    "scope": "read offline",
                }
            ),
            "",
        )
    )

    return HTTPFound(location=authorize_url)


@view_config(
    request_method="GET",
    route_name="blackboard_oauth_callback",
    renderer="lms:templates/api/blackboard/oauth2_redirect.html.jinja2",
)
def oauth2_redirect(request):
    authorization_code = request.params["code"]
    blackboard_api_client = request.find_service(name="blackboard_api_client")

    blackboard_api_client.get_token(authorization_code)

    return {}
