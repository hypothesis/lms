from lms.services.application_instance import ApplicationInstanceService
from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient
from lms.services.canvas_api.client import CanvasAPIClient
from lms.services.oauth2_token import OAuth2TokenService


def canvas_api_client_factory(_context, request):
    """
    Get a CanvasAPIClient from a pyramid request.

    :param request: Pyramid request object
    :return: An instance of CanvasAPIClient
    """
    application_instance = request.find_service(ApplicationInstanceService).get()

    developer_secret = application_instance.decrypted_developer_secret(
        request.registry.settings["aes_secret"]
    )

    basic_client = BasicClient(application_instance.lms_host())

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=request.find_service(OAuth2TokenService),
        client_id=application_instance.developer_key,
        client_secret=developer_secret,
        redirect_uri=request.route_url("canvas_api.oauth.callback"),
    )

    return CanvasAPIClient(authenticated_api)
