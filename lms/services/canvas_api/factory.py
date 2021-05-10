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
    application_instance = request.find_service(name="application_instance").get()

    canvas_host = urlparse(application_instance.lms_url).netloc
    developer_secret = application_instance.decrypted_developer_secret(
        request.registry.settings["aes_secret"]
    )

    basic_client = BasicClient(canvas_host)

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=request.find_service(name="oauth2_token"),
        client_id=application_instance.developer_key,
        client_secret=developer_secret,
        redirect_uri=request.route_url("canvas_api.oauth.callback"),
    )

    return CanvasAPIClient(authenticated_api)
