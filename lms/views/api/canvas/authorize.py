from urllib.parse import urlencode, urlparse, urlunparse

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from lms.validation import CanvasOAuthCallbackSchema


@view_defaults(feature_flag="new_oauth", permission="canvas_api", request_method="GET")
class CanvasAPIAuthorizeViews:
    def __init__(self, request):
        self.request = request
        self.ai_getter = request.find_service(name="ai_getter")
        self.canvas_api_client = request.find_service(name="canvas_api_client")

    @view_config(route_name="canvas_api.authorize")
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
                    }
                ),
                "",
            )
        )

        return HTTPFound(location=authorize_url)

    @view_config(
        route_name="canvas_oauth_callback",
        renderer="lms:templates/api/canvas/oauth2_redirect.html.jinja2",
        schema=CanvasOAuthCallbackSchema,
    )
    def oauth2_redirect(self):
        authorization_code = self.request.parsed_params["code"]

        token = self.canvas_api_client.get_token(authorization_code)
        self.canvas_api_client.save_token(*token)

        return {}
