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

    basic_client = BasicClient(ai_getter.lms_host())

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=request.find_service(name="oauth2_token"),
        client_id=ai_getter.developer_key(),
        client_secret=ai_getter.developer_secret(),
        redirect_uri=request.route_url("canvas_api.oauth.callback"),
    )

    return CanvasAPIClient(authenticated_api)
