from lms.product import Product
from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.services.grouping.service import GroupingService, GroupingServicePlugin


def service_factory(_context, request):
    # We plan to put an interface around this soon. So this won't happen here
    if request.product.family == Product.Family.BLACKBOARD:
        plugin = BlackboardGroupingPlugin(
            request.find_service(name="blackboard_api_client")
        )
    elif request.product.family == Product.Family.CANVAS:
        plugin = CanvasGroupingPlugin(request.find_service(name="canvas_api_client"))
    else:
        plugin = GroupingServicePlugin()

    return GroupingService(
        db=request.db,
        application_instance=request.find_service(
            name="application_instance"
        ).get_current(),
        plugin=plugin,
    )
