from lms.services.lti_grading._v11 import LTI11GradingService
from lms.services.lti_grading._v13 import LTI13GradingService
from lms.services.ltia_http import LTIAHTTPService


def service_factory(_context, request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()

    if application_instance.lti_version == "1.3.0":
        return LTI13GradingService(
            grading_url=request.parsed_params.get("lis_outcome_service_url"),
            ltia_service=request.find_service(LTIAHTTPService),
        )

    return LTI11GradingService(
        grading_url=request.parsed_params.get("lis_outcome_service_url"),
        http_service=request.find_service(name="http"),
        oauth1_service=request.find_service(name="oauth1"),
    )
