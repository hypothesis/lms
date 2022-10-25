from unittest.mock import sentinel

import pytest

from lms.product.product import Product


class TestProduct:
    def test_from_request(self, Plugins):
        product = Product.from_request(sentinel.request, sentinel.ai_settings)

        assert isinstance(product, Product)
        Plugins.assert_called_once_with(sentinel.request, Product.plugin_config)
        assert product.plugin == Plugins.return_value

    @pytest.fixture
    def Plugins(self, patch):
        return patch("lms.product.product.Plugins")
