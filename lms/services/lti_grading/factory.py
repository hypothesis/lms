from lms.services.lti_grading._v11 import LTI11GradingService
from lms.services.lti_grading._v13 import LTI13GradingService
from lms.services.ltia_http import LTIAHTTPService


def service_factory(_context, request):
    application_instance = request.lti_user.application_instance

    if application_instance.lti_version == "1.3.0":
        return LTI13GradingService(
            # Pick the value from the right dictionary depending on the context we are running
            # either an API call from the frontend (parsed_params) or inside an LTI launch (lti_params).
            line_item_url=request.parsed_params.get("lis_outcome_service_url")
            or request.lti_params.get("lis_outcome_service_url"),
            line_item_container_url=request.lti_params.get("lineitems"),
            ltia_service=request.find_service(LTIAHTTPService),
            product_family=request.product.family,
        )

    return LTI11GradingService(
        line_item_url=request.parsed_params.get("lis_outcome_service_url"),
        http_service=request.find_service(name="http"),
        oauth1_service=request.find_service(name="oauth1"),
    )
