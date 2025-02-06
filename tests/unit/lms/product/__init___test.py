from unittest.mock import create_autospec

import pytest
from pyramid.config import Configurator

from lms.product import includeme
from lms.product.factory import get_product_from_request


class TestIncludeMe:
    def test_it_sets_request_method(self, configurator):
        includeme(configurator)

        configurator.add_request_method.assert_called_once_with(
            get_product_from_request, name="product", property=True, reify=True
        )

    @pytest.fixture
    def configurator(self):
        return create_autospec(Configurator, spec_set=True, instance=True)
