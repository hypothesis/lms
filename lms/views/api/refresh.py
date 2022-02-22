from pyramid.view import view_config

from lms.models import ApplicationInstance
from lms.security import Permissions


@view_config(
    request_method="POST",
    route_name="api.oauth.refresh",
    permission=Permissions.API,
    renderer="json",
)
def get_refreshed_token(request):
    """
    Refresh the user's access token.

    Send a request to get a refreshed access token for the authenticated user
    and save it to the DB.
    """
    application_instance_service = request.find_service(name="application_instance")
    application_instance = application_instance_service.get_current()

    if application_instance.product == ApplicationInstance.Product.CANVAS:
        refresh_canvas_access_token(request)
    else:
        assert application_instance.product == ApplicationInstance.Product.BLACKBOARD
        refresh_blackboard_access_token(request)


def refresh_canvas_access_token(request):
    canvas_api_client = request.find_service(name="canvas_api_client")
    oauth2_token_service = request.find_service(name="oauth2_token")
    refresh_token = oauth2_token_service.get().refresh_token

    canvas_api_client.get_refreshed_token(refresh_token)


def refresh_blackboard_access_token(request):
    blackboard_api_client = request.find_service(name="blackboard_api_client")
    blackboard_api_client.refresh_access_token()
