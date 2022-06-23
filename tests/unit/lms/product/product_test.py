from unittest.mock import sentinel

import pytest

from lms.product.product import Product


class TestProduct:
    def test_from_request(self):
        with pytest.raises(NotImplementedError):
            Product.from_request(sentinel.request)
