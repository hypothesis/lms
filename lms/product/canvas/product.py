from dataclasses import dataclass

from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.product import Plugins, Product


@dataclass
class CanvasProduct(Product):
    """A product for Canvas specific settings and tweaks."""

    family = Product.Family.CANVAS

    @classmethod
    def from_request(cls, request):
        api_client = request.find_service(name="canvas_api_client")

        return cls(plugin=Plugins(grouping_service=CanvasGroupingPlugin(api_client)))
