from lms.product.family import Family
from lms.product.product import Product


def get_product_from_request(request) -> Product:
    """Get the correct product object from the provided request."""

    # pylint:disable=import-outside-toplevel
    from lms.product.blackboard import Blackboard
    from lms.product.canvas import Canvas
    from lms.product.d2l import D2L
    from lms.product.moodle import Moodle

    ai = request.lti_user.application_instance
    family = Family(request.lti_user.lti.product_family)

    product_class = {
        product.family: product for product in (Blackboard, Canvas, D2L, Moodle)
    }.get(family, Product)

    product = product_class.from_request(request, dict(ai.settings))
    product.family = family
    return product
