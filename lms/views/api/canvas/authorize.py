"""
Views for getting OAuth 2 access tokens for the Canvas API.

This module provides views for doing an OAuth 2 flow to get a Canvas API access
token for the current user:

https://canvas.instructure.com/doc/api/file.oauth.html

The received access tokens are saved to the DB and used by proxy API views to
authenticated server-to-server requests to Canvas.
"""
from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError
from pyramid.view import exception_view_config, view_config, view_defaults

from lms.services import CanvasAPIServerError
from lms.validation.authentication import BearerTokenSchema, CanvasOAuthCallbackSchema


@view_defaults(request_method="GET", route_name="canvas_oauth_callback")
class CanvasAPIAuthorizeViews:

    # The Canvas API scopes that we need for our Canvas Files feature.
    files_scopes = (
        "url:GET|/api/v1/courses/:course_id/files",
        "url:GET|/api/v1/files/:id/public_url",
    )

    # The Canvas API scopes that we need for our Sections feature.
    sections_scopes = (
        "url:GET|/api/v1/courses/:id",
        "url:GET|/api/v1/courses/:course_id/sections",
        "url:GET|/api/v1/courses/:course_id/users/:id",
    )

    def __init__(self, request):
        self.request = request

    @view_config(permission="canvas_api", route_name="canvas_api.authorize")
    def authorize(self):
        ai_getter = self.request.find_service(name="ai_getter")

        if ai_getter.canvas_sections_supported() and ai_getter.settings.get(
            "canvas", "sections_enabled"
        ):
            scopes = self.files_scopes + self.sections_scopes
        else:
            scopes = self.files_scopes

        authorize_url = urlunparse(
            (
                "https",
                urlparse(ai_getter.lms_url()).netloc,
                "login/oauth2/auth",
                "",
                urlencode(
                    {
                        "client_id": ai_getter.developer_key(),
                        "response_type": "code",
                        "redirect_uri": self.request.route_url("canvas_oauth_callback"),
                        "state": CanvasOAuthCallbackSchema(self.request).state_param(),
                        "scope": " ".join(scopes),
                    }
                ),
                "",
            )
        )

        return HTTPFound(location=authorize_url)

    @view_config(
        permission="canvas_api",
        renderer="lms:templates/api/canvas/oauth2_redirect.html.jinja2",
        schema=CanvasOAuthCallbackSchema,
    )
    def oauth2_redirect(self):
        authorization_code = self.request.parsed_params["code"]
        canvas_api_client = self.request.find_service(name="canvas_api_client")

        try:
            canvas_api_client.get_token(authorization_code)
        except CanvasAPIServerError as err:
            raise HTTPInternalServerError(
                "Authorizing with the Canvas API failed"
            ) from err

        return {}

    @exception_view_config(
        renderer="lms:templates/api/canvas/oauth2_redirect_error.html.jinja2"
    )
    @exception_view_config(
        renderer="lms:templates/api/canvas/oauth2_redirect_error.html.jinja2",
        route_name="canvas_api.authorize",
    )
    def oauth2_redirect_error(self):
        template_variables = {
            "invalid_scope": self.request.params.get("error") == "invalid_scope",
            "details": self.request.params.get("error_description"),
            "scopes": self.files_scopes + self.sections_scopes,
        }

        if self.request.lti_user:
            authorization_param = BearerTokenSchema(self.request).authorization_param(
                self.request.lti_user
            )
            template_variables["authorize_url"] = self.request.route_url(
                "canvas_api.authorize", _query=[("authorization", authorization_param)],
            )

        return template_variables
