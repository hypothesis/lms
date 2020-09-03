from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.services import NoOAuth2Token
from lms.validation.authentication import CanvasOAuthCallbackSchema


@view_config(
    request_method="GET", route_name="blackboard_api.oauth.authorize", permission="api"
)
def authorize(request):
    return HTTPFound(
        location=request.route_url(
            "blackboard_api.oauth.callback",
            _query={"state": CanvasOAuthCallbackSchema(request).state_param()},
        )
    )


@view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.callback",
    permission="api",
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
)
def oauth2_redirect(request):
    oauth2_token_service = request.find_service(name="oauth2_token")

    try:
        oauth2_token_service.get()
    except NoOAuth2Token:
        oauth2_token_service.save("fake_access_token", "fake_refresh_token", 9999)

    return {}
