"""A collection of objects which represent LMS specific details."""

from lms.product.factory import get_product_from_request
from lms.product.product import Product


def includeme(config):
    config.add_request_method(
        get_product_from_request, name="product", property=True, reify=True
    )
