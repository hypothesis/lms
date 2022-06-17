from lms.models import Product
from lms.product.grouping._blackboard import BlackboardGroupingService
from lms.product.grouping._canvas import CanvasGroupingService


def plugin_factory(_context, request):
    if request.product == Product.Family.CANVAS:
        return CanvasGroupingService(
            request.user,
            request.lti_user,
            request.find_service(name="canvas_api_client"),
        )

    if request.product == Product.Family.BLACKBOARD:
        return BlackboardGroupingService(
            request.user,
            request.lti_user,
            request.find_service(name="blackboard_api_client"),
        )

    return GroupingPlugin(request.user, request.lti_user)

    raise NotImplementedError
