from lms.resources.lti_launch.base import LTILaunchResource
from lms.resources.lti_launch.canvas import CanvasLTILaunchResource
from lms.resources.lti_launch.blackboard import BlackboardLTILaunchResource

from lms.models import ApplicationInstance


def _is_canvas(request):
    """Return True if Canvas is the LMS that launched us."""
    if (
        request.find_service(name="application_instance").get_current().product
        == ApplicationInstance.Product.CANVAS
    ):
        return True

    # TODO params only works for LTI1.1, but lti_params is part of c
    # context and that's what we are building here.
    if "custom_canvas_course_id" in request.params:
        return True

    return False


def _is_blackboard(request):
    return (
        request.find_service(name="application_instance").get_current().product
        == ApplicationInstance.Product.BLACKBOARD
    )


def service_factory(request):
    if _is_canvas(request):
        return CanvasLTILaunchResource(request)
    elif _is_blackboard(request):
        return BlackboardLTILaunchResource(request)

    return LTILaunchResource(request)
