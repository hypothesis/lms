from lms.services.blackboard_api._basic import BasicClient
from lms.services.blackboard_api.client import BlackboardAPIClient


def blackboard_api_client_factory(_context, request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()
    settings = request.registry.settings

    return BlackboardAPIClient(
        BasicClient(
            blackboard_host=application_instance.lms_host(),
            client_id=settings["blackboard_api_client_id"],
            client_secret=settings["blackboard_api_client_secret"],
            redirect_uri=request.route_url("blackboard_api.oauth.callback"),
            http_service=request.find_service(name="http"),
            oauth_http_service=request.find_service(name="oauth_http"),
        ),
        request=request,
        file_service=request.find_service(name="file"),
    )
