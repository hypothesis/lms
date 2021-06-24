from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from lms.security import Permissions
from lms.validation.authentication import OAuthCallbackSchema

from urllib.parse import urlencode, urlunparse
from lms.views import helpers


@view_config(
    request_method="GET",
    route_name="onedrive.filepicker.authorize",
    renderer="lms:templates/onedrive.html.jinja2",
)
def authorize(request):
    return {}


@view_config(
    request_method="GET",
    route_name="onedrive.oauth.authorize",
    permission=Permissions.API,
)
def oauth_authorize(request):
    client_id = request.registry.settings["onedrive_client_id"]
    state = OAuthCallbackSchema(request).state_param()

    return HTTPFound(
        location=urlunparse(
            (
                "https",
                "login.microsoftonline.com",
                "common/oauth2/v2.0/authorize",
                "",
                urlencode(
                    {
                        "client_id": client_id,
                        "scope": "files.read.all offline_access",
                        "response_type": "code",
                        "state": state,
                        "redirect_uri": request.route_url("onedrive.oauth.callback"),
                    }
                ),
                "",
            )
        )
    )


@view_config(
    request_method="GET",
    route_name="onedrive.oauth.callback",
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
    schema=OAuthCallbackSchema,
)
def oauth2_redirect(request):
    print("CALLBACK")
    print(request.params)
    request.find_service(name="onedrive").get_token(
        request.params["code"],
    )
    return {}


@view_config(request_method="GET", route_name="onedrive.files.via_url")
def via_url(request):
    """Return the Via URL for annotating the given OneDrive file."""
    onedrive = request.find_service(name="onedrive")

    return {
        "via_url": helpers.via_url(
            request,
            onedrive.download_url(
                request.params["document_url"],
            ),
            content_type="pdf",
        )
    }
