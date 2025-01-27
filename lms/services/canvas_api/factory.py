from lms.services.aes import AESService
from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient
from lms.services.canvas_api._pages import CanvasPagesClient
from lms.services.canvas_api.client import CanvasAPIClient
from lms.services.file import file_service_factory
from lms.services.oauth2_token import oauth2_token_service_factory


def canvas_api_client_factory(
    _context, request, application_instance=None, user_id=None
):
    """
    Get a CanvasAPIClient from a pyramid request.

    :param request: Pyramid request object
    :return: An instance of CanvasAPIClient
    """
    if application_instance and user_id:
        oauth2_token_service = oauth2_token_service_factory(
            _context,
            request,
            application_instance=application_instance,
            user_id=user_id,
        )
        file_service = file_service_factory(_context, request, application_instance)

    else:
        oauth2_token_service = request.find_service(name="oauth2_token")
        file_service = request.find_service(name="file")

    if not application_instance:
        application_instance = request.lti_user.application_instance

    if not user_id:
        user_id = request.lti_user.user_id

    developer_secret = application_instance.decrypted_developer_secret(
        request.find_service(AESService)
    )

    basic_client = BasicClient(application_instance.lms_host())

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=oauth2_token_service,
        client_id=application_instance.developer_key,
        client_secret=developer_secret,
        redirect_uri=request.route_url("canvas_api.oauth.callback"),
    )
    return CanvasAPIClient(
        authenticated_api,
        file_service=file_service,
        pages_client=CanvasPagesClient(authenticated_api, file_service),
        folders_enabled=application_instance.settings.get(
            "canvas", "folders_enabled", default=False
        ),
        application_instance=application_instance,
    )
