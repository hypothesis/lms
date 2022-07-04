from dataclasses import dataclass

from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class Blackboard(Product):
    """A product for Blackboard specific settings and tweaks."""

    family: Product.Family = Product.Family.BLACKBOARD

    route: Routes = Routes(
        oauth2_authorize="blackboard_api.oauth.authorize",
        oauth2_refresh="blackboard_api.oauth.refresh",
    )

    plugin_config: PluginConfig = PluginConfig(
        grouping_service=BlackboardGroupingPlugin
    )
