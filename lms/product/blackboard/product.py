from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.product import PluginConfig, Product


class Blackboard(Product):
    """A product for Blackboard specific settings and tweaks."""

    family = Product.Family.BLACKBOARD
    plugin_config = PluginConfig(grouping_service=BlackboardGroupingPlugin)
