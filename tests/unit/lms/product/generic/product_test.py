import pytest

from lms.product.generic import GenericProduct


class TestGenericProduct:
    def test_from_request(self, pyramid_request, GroupingServicePlugin):
        product = GenericProduct.from_request(pyramid_request)

        GroupingServicePlugin.assert_called_once_with()
        assert product.plugin.grouping_service == GroupingServicePlugin.return_value

    @pytest.fixture
    def GroupingServicePlugin(self, patch):
        return patch("lms.product.generic.product.GroupingServicePlugin")
