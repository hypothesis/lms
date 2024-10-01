from lms.services.lti_grading._v11 import LTI11GradingService
from lms.services.lti_grading._v13 import LTI13GradingService
from lms.services.lti_grading.interface import LTIGradingService
from lms.services.ltia_http import LTIAHTTPService


def service_factory(_context, request, application_instance=None) -> LTIGradingService:
    """Create a new LTIGradingService.

    When called via pyramid services (ie request.find_service) the LTI version is selected
    depending on the current request's application_instance.

    For other uses cases (e.g. from a Celery task) the passed application_instance will be used instead.
    """

    if not application_instance:
        application_instance = request.lti_user.application_instance

    lti_version = application_instance.lti_version
    lis_outcome_service_url = _get_lis_outcome_service_url(request)

    if lti_version == "1.3.0":
        return LTI13GradingService(
            line_item_url=lis_outcome_service_url,
            line_item_container_url=request.lti_params.get("lineitems"),
            ltia_service=request.find_service(LTIAHTTPService),
            product_family=request.product.family,
            misc_plugin=request.product.plugin.misc,
            lti_registration=application_instance.lti_registration,
        )

    return LTI11GradingService(
        line_item_url=lis_outcome_service_url,
        http_service=request.find_service(name="http"),
        oauth1_service=request.find_service(name="oauth1"),
        application_instance=request.lti_user.application_instance,
    )


def _get_lis_outcome_service_url(request) -> str | None:
    # Pick the value from the right dictionary depending on the context we are running
    # either an API call from the frontend (parsed_params) or inside an LTI launch (lti_params).
    if hasattr(request, "parsed_params") and (
        lis_outcome_service_url := request.parsed_params.get("lis_outcome_service_url")
    ):
        return lis_outcome_service_url

    return request.lti_params.get("lis_outcome_service_url")
