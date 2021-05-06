from urllib.parse import urlparse

from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient
from lms.services.canvas_api.client import CanvasAPIClient


def canvas_api_client_factory(_context, request):
    """
    Get a CanvasAPIClient from a pyramid request.

    :param request: Pyramid request object
    :return: An instance of CanvasAPIClient
    """
    ai_getter = request.find_service(name="ai_getter")
    application_instance_service = request.find_service(name="application_instance")

    canvas_host = urlparse(ai_getter.lms_url()).netloc
    basic_client = BasicClient(canvas_host)

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=request.find_service(name="oauth2_token"),
        client_id=ai_getter.developer_key(),
        client_secret=application_instance_service.developer_secret(),
        redirect_uri=request.route_url("canvas_api.oauth.callback"),
    )

    return CanvasAPIClient(authenticated_api)
