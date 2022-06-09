from lms.models import Product
from lms.services.product.grouping._blackboard import BlackboardGroupingService
from lms.services.product.grouping._canvas import CanvasGroupingService


def service_factory(_context, request):
    if request.product == Product.Family.CANVAS:
        return CanvasGroupingService(
            request.user,
            request.lti_user,
            request.find_service(name="grouping"),
            request.find_service(name="canvas_api_client"),
        )

    if request.product == Product.Family.BLACKBOARD:
        return BlackboardGroupingService(
            request.user,
            request.lti_user,
            request.find_service(name="grouping"),
            request.find_service(name="blackboard_api_client"),
        )

    raise NotImplementedError
