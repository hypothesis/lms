"""
Views for authorizing with Canvas Studio and listing videos.

See `CanvasStudioService` for more details.
"""

from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPBadRequest, HTTPFound
from pyramid.view import view_config

from lms.models.oauth2_token import Service
from lms.security import Permissions
from lms.services import CanvasStudioService
from lms.services.exceptions import OAuth2TokenError
from lms.services.oauth_http import create_service as create_oauth_http_service
from lms.validation.authentication import OAuthCallbackSchema
from lms.views.helpers import via_video_url


# View for authorization popup which redirects to Canvas Studio's OAuth
# authorization endpoint.
#
# Canvas Studio's OAuth implementation has several issues which complicate
# using the standard OAuth flow:
#
# 1. Canvas Studio does not return the `state` parameter to us when it redirects
#    after a successful authorization [1].
# 2. Canvas Studio does not allow the use of unencrypted HTTP or `localhost`
#    as a redirect URL for an OAuth client.
#
# To work around these issues, we use the following authentication flow:
#
# 1. User clicks button in UI to initiate Canvas Studio authorization
# 2. The button opens `/api/canvas_studio/oauth/authorize` in a popup
# 3. In development only, the popup redirects to change the host from
#    http://localhost:8001 to https://hypothesis.local:48001/, keeping the
#    path the same.
# 4. The popup returns a 200 response which sets a cookie and does a client-side
#    redirect to the Canvas Studio authorization endpoint.
#
#    We use a client-side redirect because setting cookies as part of a 302
#    redirect response does not work in some browsers (including Chrome).
# 5. The user completes authorization in the Canvas Studio UI
# 6. Canvas Studio redirects to our `/api/canvas_studio/oauth/callback`
#    endpoint, passing the authorization code, but not the `state`.
# 7. We read the `state` parameter out of the cookie and then
#    redirect to the `/api/canvas_studio/oauth/callback` URL that Canvas Studio
#    should have used.
#
# [1] https://community.canvaslms.com/t5/Canvas-Developers-Group/Canvas-Studio-OAuth-authorization-does-not-send-state-parameter/td-p/596747
@view_config(
    request_method="GET",
    route_name="canvas_studio_api.oauth.authorize",
    renderer="lms:templates/api/oauth2/client_side_redirect.html.jinja2",
    permission=Permissions.API,
)
def authorize(request):
    if request.host_url == "http://localhost:8001":
        redirect_url = request.url.replace(
            request.host_url, "https://hypothesis.local:48001"
        )
        return HTTPFound(location=redirect_url)

    canvas_studio_svc = request.find_service(CanvasStudioService)
    oauth_state = OAuthCallbackSchema(request).state_param()
    auth_url = canvas_studio_svc.authorization_url(oauth_state)

    request.response.set_cookie("canvas_studio_oauth_state", oauth_state)

    return {"redirect_url": auth_url, "link_text": "Canvas Studio login"}


@view_config(
    request_method="GET",
    route_name="canvas_studio_api.oauth.callback",
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
    request_param="state",
    schema=OAuthCallbackSchema,
)
def oauth2_redirect(request):
    code = request.parsed_params["code"]
    request.find_service(CanvasStudioService).get_access_token(code)
    return {}


@view_config(
    request_method="GET",
    route_name="canvas_studio_api.oauth.callback",
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
)
def oauth2_redirect_missing_state(request):
    code = request.params["code"]
    state = request.cookies.get("canvas_studio_oauth_state")

    # Generate the redirect URL which Canvas Studio should have generated.
    url = request.route_url(
        "canvas_studio_api.oauth.callback", _query={"code": code, "state": state}
    )

    return HTTPFound(location=url)


@view_config(
    request_method="GET",
    route_name="canvas_studio_api.videos.list",
    renderer="json",
    permission=Permissions.API,
)
def list_videos(request):
    svc = request.find_service(CanvasStudioService)
    return svc.list_video_library()


@view_config(
    request_method="GET",
    route_name="canvas_studio_api.collections.videos.list",
    renderer="json",
    permission=Permissions.API,
)
def list_collection(request):
    svc = request.find_service(CanvasStudioService)
    collection_id = request.matchdict["collection_id"]
    return svc.list_collection(collection_id)


@view_config(
    request_method="GET",
    route_name="canvas_studio_api.via_url",
    renderer="json",
    permission=Permissions.API,
)
def via_url(request):
    svc = request.find_service(CanvasStudioService)
    document_url = request.params.get("document_url")
    media_id = (
        CanvasStudioService.media_id_from_url(document_url) if document_url else None
    )
    if not media_id:
        raise HTTPBadRequest("Missing or invalid `document_url` param")

    canonical_url = svc.get_canonical_video_url(media_id)
    download_url = svc.get_video_download_url(media_id)

    # TODO - Handle case where transcript is not available.
    transcript_url = svc.get_transcript_url(media_id)

    via_url = via_video_url(request, canonical_url, download_url, transcript_url)

    return {"via_url": via_url}
