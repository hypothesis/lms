import pytest

from lms.product.canvas import CanvasProduct


class TestCanvasProduct:
    def test_from_request(
        self, pyramid_request, canvas_api_client, CanvasGroupingPlugin
    ):
        product = CanvasProduct.from_request(pyramid_request)

        CanvasGroupingPlugin.assert_called_once_with(canvas_api_client)
        assert product.plugin.grouping_service == CanvasGroupingPlugin.return_value

    @pytest.fixture
    def CanvasGroupingPlugin(self, patch):
        return patch("lms.product.canvas.product.CanvasGroupingPlugin")
