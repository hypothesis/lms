from lms.product.blackboard import BlackboardProduct
from lms.product.canvas import CanvasProduct
from lms.product.generic import GenericProduct
from lms.product.product import Product


def get_product_from_request(request):
    family = _get_family(request)
    product_class = _get_implementing_class(family)
    product = product_class.from_request(request)
    product.family = family
    return product


def _get_implementing_class(family):
    for lms_class in Product.__subclasses__():
        if lms_class.family == family:
            return lms_class

    return GenericProduct


def _get_family(request):
    # If we are in an API request, where we are forwarding the product type ourselves
    if request.content_type == "application/json":
        return Product.Family(request.json["lms"]["product"])

    # In an LTI launch we'll use the parameters available to guess
    if product_name := request.lti_params.get("tool_consumer_info_product_family_code"):
        return Product.Family(product_name)

    # If we don't get a hint from LTI check a canvas specific parameter
    if "custom_canvas_course_id" in request.lti_params:
        return Product.Family.CANVAS

    return Product.Family.UNKNOWN
