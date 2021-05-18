from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.security import Permissions
from lms.services import NoOAuth2Token
from lms.validation.authentication import OAuthCallbackSchema


@view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.authorize",
    permission=Permissions.API,
)
def authorize(request):
    return HTTPFound(
        location=request.route_url(
            "blackboard_api.oauth.callback",
            _query={"state": OAuthCallbackSchema(request).state_param()},
        )
    )


@view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.callback",
    permission=Permissions.API,
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
)
def oauth2_redirect(request):
    oauth2_token_service = request.find_service(name="oauth2_token")

    try:
        oauth2_token_service.get()
    except NoOAuth2Token:
        oauth2_token_service.save("fake_access_token", "fake_refresh_token", 9999)

    return {}
