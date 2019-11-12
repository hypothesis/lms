from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError
from pyramid.view import exception_view_config, view_config, view_defaults

from lms.services import CanvasAPIServerError
from lms.validation.authentication import BearerTokenSchema, CanvasOAuthCallbackSchema


@view_defaults(request_method="GET", route_name="canvas_oauth_callback")
class CanvasAPIAuthorizeViews:
    def __init__(self, request):
        self.request = request
        self.ai_getter = request.find_service(name="ai_getter")

    @view_config(permission="canvas_api", route_name="canvas_api.authorize")
    def authorize(self):
        consumer_key = self.request.lti_user.oauth_consumer_key
        authorize_url = urlunparse(
            (
                "https",
                urlparse(self.ai_getter.lms_url(consumer_key)).netloc,
                "login/oauth2/auth",
                "",
                urlencode(
                    {
                        "client_id": self.ai_getter.developer_key(consumer_key),
                        "response_type": "code",
                        "redirect_uri": self.request.route_url("canvas_oauth_callback"),
                        "state": CanvasOAuthCallbackSchema(self.request).state_param(),
                        "scope": "url:GET|/api/v1/courses/:course_id/files url:GET|/api/v1/files/:id/public_url",
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
        self.request.response.status_code = 500

        authorization_param = (
            BearerTokenSchema(self.request).authorization_param(self.request.lti_user),
        )
        return {
            "authorize_url": self.request.route_url(
                "canvas_api.authorize", _query=[("authorization", authorization_param)]
            )
        }
