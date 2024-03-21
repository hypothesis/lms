from lms.product.blackboard import Blackboard
from lms.product.canvas import Canvas
from lms.product.d2l import D2L
from lms.product.family import Family
from lms.product.moodle import Moodle
from lms.product.product import Product

_PRODUCT_MAP = {
    product.family: product for product in (Blackboard, Canvas, D2L, Moodle)
}


def get_product_from_request(request) -> Product:
    """Get the correct product object from the provided request."""
    ai = request.lti_user.application_instance
    family = Family(request.lti_user.lti.product_family)

    product = _PRODUCT_MAP.get(family, Product).from_request(request, dict(ai.settings))
    product.family = family
    return product
