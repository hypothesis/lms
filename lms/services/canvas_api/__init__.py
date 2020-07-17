from urllib.parse import urlparse

from lms.services.canvas_api.authenticated import AuthenticatedClient
from lms.services.canvas_api.basic import BasicClient
from lms.services.canvas_api.public import CanvasAPIClient
from lms.services.canvas_api.token_store import TokenStore


def canvas_api_client_factory(_context, request):
    """
    Get a CanvasAPIClient from a pyramid request.

    :param _context: Pyramid context object
    :param request: Pyramid request object
    :return: An instance of CanvasAPIClient
    """
    ai_getter = request.find_service(name="ai_getter")

    canvas_host = urlparse(ai_getter.lms_url()).netloc
    basic_client = BasicClient(canvas_host)

    token_store = TokenStore(
        consumer_key=request.lti_user.oauth_consumer_key,
        user_id=request.lti_user.user_id,
        db=request.db,
    )

    authenticated_api = AuthenticatedClient(
        basic_client=basic_client,
        token_store=token_store,
        client_id=ai_getter.developer_key(),
        client_secret=ai_getter.developer_secret(),
        redirect_uri=request.route_url("canvas_oauth_callback"),
    )

    return CanvasAPIClient(authenticated_api)
