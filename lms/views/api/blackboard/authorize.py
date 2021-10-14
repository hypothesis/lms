from urllib.parse import urlencode, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import exception_view_config, view_config

from lms.security import Permissions
from lms.validation.authentication import OAuthCallbackSchema


@view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.authorize",
    permission=Permissions.API,
)
def authorize(request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()
    client_id = request.registry.settings["blackboard_api_client_id"]
    state = OAuthCallbackSchema(request).state_param()

    return HTTPFound(
        location=urlunparse(
            (
                "https",
                application_instance.lms_host(),
                "learn/api/public/v1/oauth2/authorizationcode",
                "",
                urlencode(
                    {
                        "client_id": client_id,
                        "response_type": "code",
                        "redirect_uri": request.route_url(
                            "blackboard_api.oauth.callback"
                        ),
                        "state": state,
                        "scope": "read offline",
                    }
                ),
                "",
            )
        )
    )


@view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.callback",
    permission=Permissions.API,
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
    schema=OAuthCallbackSchema,
)
def oauth2_redirect(request):
    request.find_service(name="blackboard_api_client").get_token(request.params["code"])
    return {}


@exception_view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.callback",
    renderer="lms:templates/api/oauth2/redirect_error.html.jinja2",
)
@exception_view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.authorize",
    renderer="lms:templates/api/oauth2/redirect_error.html.jinja2",
)
def oauth2_redirect_error(request):
    request.context.js_config.enable_oauth2_redirect_error_mode(
        error_code=request.context.js_config.ErrorCode.BLACKBOARD_MISSING_INTEGRATION
        if request.params.get("error_description")
        in ["Application not enabled for site", "Application not registered with site"]
        else None,
        auth_route="blackboard_api.oauth.authorize",
    )

    return {}
