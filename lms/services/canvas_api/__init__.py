from urllib.parse import urlparse

from lms.services.canvas_api.authenticated_client import CanvasAPIAuthenticatedClient
from lms.services.canvas_api.basic_client import CanvasAPIBasicClient
from lms.services.canvas_api.public_client import CanvasAPIClient
from lms.services.canvas_api.token_store import TokenStore


def canvas_api_client_factory(context_, request):
    ai_getter = request.find_service(name="ai_getter")

    canvas_host = urlparse(ai_getter.lms_url()).netloc
    basic_client = CanvasAPIBasicClient(canvas_host)

    token_store = TokenStore(
        consumer_key=request.lti_user.oauth_consumer_key,
        user_id=request.lti_user.user_id,
        db=request.db,
    )

    authenticated_api = CanvasAPIAuthenticatedClient(
        basic_api=basic_client,
        token_store=token_store,
        client_id=ai_getter.developer_key(),
        client_secret=ai_getter.developer_secret(),
        redirect_uri=request.route_url("canvas_oauth_callback"),
    )

    return CanvasAPIClient(authenticated_api)
