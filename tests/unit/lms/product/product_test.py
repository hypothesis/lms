from unittest.mock import sentinel

from lms.product.product import Product


class TestProduct:
    def test_from_request(self):
        product = Product.from_request(sentinel.request)

        assert isinstance(product, Product)
        assert product.family == Product.Family.UNKNOWN
