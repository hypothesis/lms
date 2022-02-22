from pyramid.view import view_config, view_defaults

from lms.security import Permissions


@view_defaults(request_method="POST", permission=Permissions.API, renderer="json")
class RefreshViews:
    """Get a refreshed access token for the authenticated user and save it to the DB."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(route_name="canvas_api.oauth.refresh")
    def get_refreshed_token_from_canvas(self):
        canvas_api_client = self.request.find_service(name="canvas_api_client")
        oauth2_token_service = self.request.find_service(name="oauth2_token")
        refresh_token = oauth2_token_service.get().refresh_token

        canvas_api_client.get_refreshed_token(refresh_token)

    @view_config(route_name="blackboard_api.oauth.refresh")
    def get_refreshed_token_from_blackboard(self):
        blackboard_api_client = self.request.find_service(name="blackboard_api_client")
        blackboard_api_client.refresh_access_token()
