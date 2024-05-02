"""
Views for getting OAuth 2 access tokens for the Canvas API.

This module provides views for doing an OAuth 2 flow to get a Canvas API access
token for the current user:

https://canvas.instructure.com/doc/api/file.oauth.html

The received access tokens are saved to the DB and used by proxy API views to
authenticated server-to-server requests to Canvas.
"""

from urllib.parse import urlencode, urlunparse

from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError
from pyramid.view import exception_view_config, view_config

from lms.events import LTIEvent
from lms.security import Permissions
from lms.services import CanvasAPIServerError, EventService
from lms.validation.authentication import OAuthCallbackSchema

SCOPES = {
    # Support for assignments using Canvas files
    "files": (
        "url:GET|/api/v1/courses/:course_id/files",
        "url:GET|/api/v1/files/:id/public_url",
    ),
    # Support for folders in Canvas file picker
    "folders": ("url:GET|/api/v1/courses/:course_id/folders",),
    # Assignment groups using Canvas groups
    "groups": (
        "url:GET|/api/v1/courses/:course_id/group_categories",
        "url:GET|/api/v1/courses/:course_id/groups",
        "url:GET|/api/v1/group_categories/:group_category_id/groups",
    ),
    # Support for assignments using Canvas pages
    "pages": (
        "url:GET|/api/v1/courses/:course_id/pages",
        "url:GET|/api/v1/courses/:course_id/pages/:url_or_id",
    ),
    # Assignment groups using Canvas sections
    "sections": (
        "url:GET|/api/v1/courses/:course_id/sections",
        "url:GET|/api/v1/courses/:course_id/users/:id",
        "url:GET|/api/v1/courses/:id",
    ),
}

# All the scopes that our LMS app may use.
ALL_SCOPES = {scope for scopes in SCOPES.values() for scope in scopes}


@view_config(
    request_method="GET",
    route_name="canvas_api.oauth.authorize",
    permission=Permissions.API,
)
def authorize(request):
    application_instance = request.lti_user.application_instance
    course_service = request.find_service(name="course")

    scopes = SCOPES["files"]

    if application_instance.settings.get("canvas", "folders_enabled"):
        scopes += SCOPES["folders"]

    if application_instance.settings.get("canvas", "pages_enabled"):
        scopes += SCOPES["pages"]

    if application_instance.developer_key and (
        # If the instance could add a new course with sections...
        application_instance.settings.get("canvas", "sections_enabled")
        # ... or any of it's existing courses have sections
        or course_service.any_with_setting("canvas", "sections_enabled", True)
    ):
        scopes += SCOPES["sections"]

    if application_instance.settings.get("canvas", "groups_enabled"):
        scopes += SCOPES["groups"]

    auth_url = urlunparse(
        (
            "https",
            application_instance.lms_host(),
            "login/oauth2/auth",
            "",
            urlencode(
                {
                    "client_id": application_instance.developer_key,
                    "response_type": "code",
                    "redirect_uri": request.route_url("canvas_api.oauth.callback"),
                    "state": OAuthCallbackSchema(request).state_param(),
                    "scope": " ".join(scopes),
                }
            ),
            "",
        )
    )

    return HTTPFound(location=auth_url)


@view_config(
    request_method="GET",
    route_name="canvas_api.oauth.callback",
    permission=Permissions.API,
    renderer="lms:templates/api/oauth2/redirect.html.jinja2",
    schema=OAuthCallbackSchema,
)
def oauth2_redirect(request):
    authorization_code = request.parsed_params["code"]
    canvas_api_client = request.find_service(name="canvas_api_client")

    try:
        canvas_api_client.get_token(authorization_code)
    except CanvasAPIServerError as err:
        raise HTTPInternalServerError("Authorizing with the Canvas API failed") from err

    return {}


@exception_view_config(
    request_method="GET",
    route_name="canvas_api.oauth.callback",
    renderer="lms:templates/api/oauth2/redirect_error.html.jinja2",
)
@exception_view_config(
    request_method="GET",
    route_name="canvas_api.oauth.authorize",
    renderer="lms:templates/api/oauth2/redirect_error.html.jinja2",
    # Explicitly declare the need for a transaction for exception view.
    # While this view doesn't write any data to the DB it
    # could issue queries to generate the Event object.
    tm_active=True,
)
def oauth2_redirect_error(request):
    kwargs = {
        "auth_route": "canvas_api.oauth.authorize",
        "canvas_scopes": list(ALL_SCOPES),
    }
    if request.params.get("error") == "invalid_scope":
        error_code = request.context.js_config.ErrorCode.CANVAS_INVALID_SCOPE
        kwargs["error_code"] = error_code

        EventService.queue_event(
            LTIEvent.from_request(
                request=request,
                type_=LTIEvent.Type.ERROR_CODE,
                data={"code": error_code},
            )
        )

    if error_description := request.params.get("error_description"):
        kwargs["error_details"] = {"error_description": error_description}

    request.context.js_config.enable_oauth2_redirect_error_mode(**kwargs)

    return {}
