from urllib.parse import urlencode, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config

from lms.security import Permissions
from lms.services.d2l_api import D2LAPIClient
from lms.validation.authentication import OAuthCallbackSchema


@view_config(
    request_method="GET",
    route_name="d2l_api.oauth.authorize",
    permission=Permissions.API,
)
def authorize(request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()
    state = OAuthCallbackSchema(request).state_param()

    return HTTPFound(
        location=urlunparse(
            (
                "https",
                "auth.brightspace.com",
                "oauth2/auth",
                "",
                urlencode(
                    {
                        "client_id": application_instance.settings.get(
                            "desire2learn", "client_id"
                        ),
                        "response_type": "code",
                        "redirect_uri": request.route_url("d2l_api.oauth.callback"),
                        "state": state,
                        "scope": " ".join(
                            [
                                "core:*:*",
                                "groups:*:*",
                            ]
                        ),
                    }
                ),
                "",
            )
        )
    )


@view_config(
    request_method="GET",
    route_name="d2l_api.oauth.callback",
    permission=Permissions.API,
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
    schema=OAuthCallbackSchema,
)
def oauth2_redirect(request):
    request.find_service(D2LAPIClient).get_token(request.params["code"])
    return {}


@exception_view_config(
    request_method="GET",
    route_name="d2l_api.oauth.callback",
    renderer="lms:templates/api/oauth2/redirect_error.html.jinja2",
)
@exception_view_config(
    request_method="GET",
    route_name="d2l_api.oauth.authorize",
    renderer="lms:templates/api/oauth2/redirect_error.html.jinja2",
)
def oauth2_redirect_error(request):
    request.context.js_config.enable_oauth2_redirect_error_mode(
        auth_route="d2l_api.oauth.authorize"
    )

    return {}
