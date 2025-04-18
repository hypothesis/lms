from lms.models.family import Family
from lms.product.product import Product


def get_product_from_request(request) -> Product:
    """Get the correct product object from the provided request."""

    from lms.product.blackboard import Blackboard
    from lms.product.canvas import Canvas
    from lms.product.d2l import D2L
    from lms.product.moodle import Moodle

    family = Family.UNKNOWN
    settings = {}
    if request.lti_user:
        ai = request.lti_user.application_instance
        family = Family(request.lti_user.lti.product_family)
        settings = ai.settings

    product_class = {
        product.family: product for product in (Blackboard, Canvas, D2L, Moodle)
    }.get(family, Product)

    product = product_class.from_request(request, dict(settings))
    product.family = family
    return product
