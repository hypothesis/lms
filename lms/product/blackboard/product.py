from dataclasses import dataclass

from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.product import Plugins, Product


@dataclass
class BlackboardProduct(Product):
    """A product for Blackboard specific settings and tweaks."""

    family: Product.Family = Product.Family.BLACKBOARD

    @classmethod
    def from_request(cls, request):
        api_client = request.find_service(name="blackboard_api_client")

        return cls(
            plugin=Plugins(grouping_service=BlackboardGroupingPlugin(api_client))
        )
