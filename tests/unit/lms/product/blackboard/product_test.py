import pytest

from lms.product.blackboard import BlackboardProduct


class TestBlackboardProduct:
    def test_from_request(
        self, pyramid_request, blackboard_api_client, BlackboardGroupingPlugin
    ):
        product = BlackboardProduct.from_request(pyramid_request)

        BlackboardGroupingPlugin.assert_called_once_with(blackboard_api_client)
        assert product.plugin.grouping_service == BlackboardGroupingPlugin.return_value

    @pytest.fixture
    def BlackboardGroupingPlugin(self, patch):
        return patch("lms.product.blackboard.product.BlackboardGroupingPlugin")
