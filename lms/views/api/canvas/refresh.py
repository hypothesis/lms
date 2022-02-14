from pyramid.view import view_config

from lms.security import Permissions


@view_config(
    request_method="POST",
    route_name="canvas_api.oauth.refresh",
    permission=Permissions.API,
    renderer="json",
)
def get_refreshed_token(request):
    """
    Refresh the user's access token.

    Send a request to Canvas to get a refreshed access token for the
    authenticated user and save it to the DB.
    """
    canvas_api = request.find_service(name="canvas_api_client")
    oauth2_token_service = request.find_service(name="oauth2_token")

    refresh_token = oauth2_token_service.get().refresh_token

    canvas_api.get_refreshed_token(refresh_token)
