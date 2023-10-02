from lms.services.aes import AESService
from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient
from lms.services.canvas_api._pages import CanvasPagesClient
from lms.services.canvas_api.client import CanvasAPIClient


def canvas_api_client_factory(_context, request):
    """
    Get a CanvasAPIClient from a pyramid request.

    :param request: Pyramid request object
    :return: An instance of CanvasAPIClient
    """
    application_instance = request.lti_user.application_instance

    developer_secret = application_instance.decrypted_developer_secret(
        request.find_service(AESService)
    )

    basic_client = BasicClient(application_instance.lms_host())

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=request.find_service(name="oauth2_token"),
        client_id=application_instance.developer_key,
        client_secret=developer_secret,
        redirect_uri=request.route_url("canvas_api.oauth.callback"),
    )
    file_service = request.find_service(name="file")

    return CanvasAPIClient(
        authenticated_api,
        file_service=file_service,
        pages_client=CanvasPagesClient(authenticated_api, file_service),
        folders_enabled=application_instance.settings.get(
            "canvas", "folders_enabled", default=False
        ),
    )
