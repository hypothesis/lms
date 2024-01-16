from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.d2l import D2L
from lms.product.moodle import Moodle
from lms.product.product import Product

_PRODUCT_MAP = {
    product.family: product for product in (Blackboard, Canvas, D2L, Moodle)
}


def get_product_from_request(request) -> Product:
    """Get the correct product object from the provided request."""
    ai = request.lti_user.application_instance if request.lti_user else None

    family = _get_family(request, ai)
    product = _PRODUCT_MAP.get(family, Product).from_request(
        request, dict(ai.settings) if ai else {}
    )
    product.family = family
    return product


def _get_family(
    request, application_instance
):  # pylint:disable=too-many-return-statements
    # First, if we are in an LMS specific route, return that
    # These are generally GET routes where we don't pass the `product` parameter back to us
    if request.matched_route.name.startswith("canvas_api."):
        return Product.Family.CANVAS

    if request.matched_route.name.startswith("blackboard_api."):
        return Product.Family.BLACKBOARD

    # If we are in an API request, where we are forwarding the product type ourselves
    if request.content_type == "application/json" and "lms" in request.json:
        return Product.Family(request.json["lms"]["product"])

    # In an LTI launch we'll use the parameters available to guess
    if product_name := request.lti_params.get("tool_consumer_info_product_family_code"):
        return Product.Family(product_name)

    # If we don't get a hint from LTI check a canvas specific parameter
    if "custom_canvas_course_id" in request.lti_params:
        return Product.Family.CANVAS

    # Finally try to match using the stored family_code in the application instance
    # We use this in LTIOutcomesViews
    if application_instance:
        return Product.Family(
            application_instance.tool_consumer_info_product_family_code
        )

    return Product.Family.UNKNOWN
