from urllib.parse import urlencode, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.security import Permissions
from lms.services import ApplicationInstanceService, BlackboardAPIClient
from lms.validation.authentication import OAuthCallbackSchema


@view_config(
    request_method="GET",
    route_name="blackboard_api.oauth.authorize",
    permission=Permissions.API,
)
def authorize(request):
    application_instance = request.find_service(ApplicationInstanceService).get()
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
    request.find_service(BlackboardAPIClient).get_token(request.params["code"])
    return {}
