"""
Views for authorizing with Canvas Studio and listing videos.

See `CanvasStudioService` for more details.
"""

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.security import Permissions
from lms.services import CanvasStudioService
from lms.services.canvas_studio import replace_localhost_in_url
from lms.services.exceptions import SerializableError
from lms.validation.authentication import OAuthCallbackSchema
from lms.views.helpers import via_video_url


class CanvasStudioLaunchError(SerializableError):
    """
    An error occurred while launching a Canvas Studio assignment.

    This exception is used for non-authorization errors that prevent a
    Canvas Studio assignment from being launched.
    """

    def __init__(self, error_code: str, message: str):
        super().__init__(error_code=error_code, message=message)


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
# To make step (3) work for local development, add `hypothesis.local` as an
# alias for `127.0.0.1` in /etc/hosts.
#
# [1] https://community.canvaslms.com/t5/Canvas-Developers-Group/Canvas-Studio-OAuth-authorization-does-not-send-state-parameter/td-p/596747
@view_config(
    request_method="GET",
    route_name="canvas_studio_api.oauth.authorize",
    renderer="lms:templates/api/oauth2/client_side_redirect.html.jinja2",
    permission=Permissions.API,
)
def authorize(request):
    updated_url = replace_localhost_in_url(request.url)
    if updated_url != request.url:
        return HTTPFound(location=updated_url)

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
    route_name="canvas_studio_api.media.list",
    renderer="json",
    permission=Permissions.API,
)
def list_media(request):
    svc = request.find_service(CanvasStudioService)
    return svc.list_media_library()


@view_config(
    request_method="GET",
    route_name="canvas_studio_api.collections.media.list",
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
    assignment = request.find_service(name="assignment").get_assignment(
        request.lti_user.application_instance.tool_consumer_instance_guid,
        request.lti_user.lti.assignment_id,
    )
    document_url = assignment.document_url
    media_id = CanvasStudioService.media_id_from_url(document_url)
    if not media_id:
        raise CanvasStudioLaunchError(
            "canvas_studio_media_not_found",
            "Unable to get Canvas Studio media ID",  # noqa: EM101
        )

    svc = request.find_service(CanvasStudioService)
    canonical_url = svc.get_canonical_video_url(media_id)

    # Get the video download URL, then the transcript. We do things in this
    # order because if the video cannot be used (eg. because it is a Vimeo
    # upload), there is no point in the user uploading a transcript, if that is
    # also missing.

    download_url = svc.get_video_download_url(media_id)
    if not download_url:
        raise CanvasStudioLaunchError(
            "canvas_studio_download_unavailable",  # noqa: EM101
            "Hypothesis was unable to fetch the video",
        )

    transcript_url = svc.get_transcript_url(media_id)
    if not transcript_url:
        raise CanvasStudioLaunchError(
            "canvas_studio_transcript_unavailable",  # noqa: EM101
            "This video does not have a published transcript",
        )

    return {
        "via_url": via_video_url(request, canonical_url, download_url, transcript_url)
    }
