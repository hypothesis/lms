"""A collection of objects which represent LMS specific details."""

from lms.product.factory import get_product_from_request
from lms.product.product import Product


def includeme(config):
    # Register the default plugins
    config.include("lms.product.plugin")

    # Give everyone a chance to register their plugins etc.
    config.include("lms.product.blackboard")
    config.include("lms.product.canvas")
    config.include("lms.product.d2l")
    config.include("lms.product.moodle")

    # Add the `request.product` method
    config.add_request_method(
        get_product_from_request, name="product", property=True, reify=True
    )
