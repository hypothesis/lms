from lms.services.lti_grading._v11 import LTI11GradingService


def service_factory(_context, request):
    return LTI11GradingService(
        grading_url=request.parsed_params["lis_outcome_service_url"],
        http_service=request.find_service(name="http"),
        oauth1_service=request.find_service(name="oauth1"),
    )
