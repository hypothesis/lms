from lms.product.product import Product


def includeme(config):
    config.add_request_method(
        Product.from_request, name="product", property=True, reify=True
    )
