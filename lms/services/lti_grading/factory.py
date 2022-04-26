from lms.services.lti_grading._v11 import LTI11GradingClient
from lms.services.lti_grading._v13 import LTI13GradingClient
from lms.services import LTIAHTTPService


def factory(_context, request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()

    if application_instance.lti_version == "1.3.0":
        return LTI13GradingClient(
            grading_url=request.parsed_params["lis_outcome_grading_url"],
            ltia_service=request.find_service(LTIAHTTPService),
        )

    return LTI11GradingClient(
        grading_url=request.parsed_params["lis_outcome_grading_url"],
        http_service=request.find_service(name="http"),
        oauth1_service=request.find_service(name="oauth1"),
    )
