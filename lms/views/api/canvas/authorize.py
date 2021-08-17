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

from lms.security import Permissions
from lms.services import CanvasAPIServerError
from lms.validation.authentication import OAuthCallbackSchema

#: The Canvas API scopes that we need for our Canvas Files feature.
FILES_SCOPES = (
    "url:GET|/api/v1/courses/:course_id/files",
    "url:GET|/api/v1/files/:id/public_url",
)

#: The Canvas API scopes that we need for our Sections feature.
SECTIONS_SCOPES = (
    "url:GET|/api/v1/courses/:id",
    "url:GET|/api/v1/courses/:course_id/sections",
    "url:GET|/api/v1/courses/:course_id/users/:id",
)

GROUPS_SCOPES = (
    "url:GET|/api/v1/courses/:course_id/group_categories",
    "url:GET|/api/v1/group_categories/:group_category_id/groups",
    "url:GET|/api/v1/courses/:course_id/groups",
)


@view_config(
    request_method="GET",
    route_name="canvas_api.oauth.authorize",
    permission=Permissions.API,
)
def authorize(request):
    application_instance = request.find_service(name="application_instance").get()
    course_service = request.find_service(name="course")

    scopes = FILES_SCOPES

    if application_instance.developer_key and (
        # If the instance could add a new course with sections...
        application_instance.settings.get("canvas", "sections_enabled")
        # ... or any of it's existing courses have sections
        or course_service.any_with_setting("canvas", "sections_enabled", True)
    ):
        scopes += SECTIONS_SCOPES

    if application_instance.settings.get("canvas", "groups_enabled"):
        scopes += GROUPS_SCOPES

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
)
def oauth2_redirect_error(request):
    request.context.js_config.enable_oauth2_redirect_error_mode(
        auth_route="canvas_api.oauth.authorize",
        error_details=request.params.get("error_description"),
        error_code=request.context.js_config.ErrorCode.CANVAS_INVALID_SCOPE
        if request.params.get("error") == "invalid_scope"
        else None,
        canvas_scopes=FILES_SCOPES + SECTIONS_SCOPES + GROUPS_SCOPES,
    )

    return {}
