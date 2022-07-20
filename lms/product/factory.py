from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.product import Product
from lms.services.application_instance import ApplicationInstanceNotFound

_PRODUCT_MAP = {product.family: product for product in (Blackboard, Canvas)}


def get_product_from_request(request) -> Product:
    """Get the correct product object from the provided request."""

    family = _get_family(request)
    product = _PRODUCT_MAP.get(family, Product).from_request(request)
    product.family = family
    return product


def _get_family(request):  # pylint:disable=too-many-return-statements
    # First, if we are in an LMS specific route, return that
    # These are generally GET routes where we don't pass the `product` parameter back to us
    if request.matched_route.name.startswith("canvas_api."):
        return Product.Family.CANVAS

    if request.matched_route.name.startswith("blackboard_api."):
        return Product.Family.BLACKBOARD

    # If we are in an API request, where we are forwarding the product type ourselves
    if request.content_type == "application/json":
        return Product.Family(request.json["lms"]["product"])

    # In an LTI launch we'll use the parameters available to guess
    if product_name := request.lti_params.get("tool_consumer_info_product_family_code"):
        return Product.Family(product_name)

    # If we don't get a hint from LTI check a canvas specific parameter
    if "custom_canvas_course_id" in request.lti_params:
        return Product.Family.CANVAS

    # Finally try to match using the stored family_code in the application instance
    # We use this in LTIOutcomesViews
    try:
        application_instance = request.find_service(
            name="application_instance"
        ).get_current()
        return Product.Family(
            application_instance.tool_consumer_info_product_family_code
        )
    except ApplicationInstanceNotFound:
        return Product.Family.UNKNOWN
