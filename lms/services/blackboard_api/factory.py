from lms.services.blackboard_api.client import BlackboardAPIClient


def blackboard_api_client_factory(_context, request):
    return BlackboardAPIClient(request.find_service(name="basic_blackboard_api_client"))
