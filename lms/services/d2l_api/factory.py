from lms.services.aes import AESService
from lms.services.d2l_api._basic import BasicClient
from lms.services.d2l_api.client import D2LAPIClient


def d2l_api_client_factory(_context, request):
    application_instance = request.lti_user.application_instance

    return D2LAPIClient(
        BasicClient(
            lms_host=application_instance.lms_host(),
            client_id=application_instance.settings.get("desire2learn", "client_id"),
            client_secret=application_instance.settings.get_secret(
                request.find_service(AESService), "desire2learn", "client_secret"
            ),
            redirect_uri=request.route_url("d2l_api.oauth.callback"),
            http_service=request.find_service(name="http"),
            oauth_http_service=request.find_service(name="oauth_http"),
        ),
        file_service=request.find_service(name="file"),
        lti_user=request.lti_user,
    )
