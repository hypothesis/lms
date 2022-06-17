from lms.models import Product
from lms.services.grouping._plugin.blackboard import BlackboardGroupingPlugin
from lms.services.grouping._plugin.canvas import CanvasGroupingPlugin
from lms.services.grouping.service import GroupingService, GroupingServicePlugin


def factory(_context, request):
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
