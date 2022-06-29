from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


class Blackboard(Product):
    """A product for Blackboard specific settings and tweaks."""

    family = Product.Family.BLACKBOARD

    route = Routes(
        oauth2_authorize="blackboard_api.oauth.authorize",
        oauth2_refresh="blackboard_api.oauth.refresh",
    )

    plugin_config = PluginConfig(grouping_service=BlackboardGroupingPlugin)
