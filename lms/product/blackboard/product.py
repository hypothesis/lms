from dataclasses import dataclass

from lms.product.blackboard._plugin.course_copy import BlackboardCourseCopyPlugin
from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.blackboard._plugin.misc import BlackboardMiscPlugin
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
        grouping=BlackboardGroupingPlugin,
        course_copy=BlackboardCourseCopyPlugin,
        misc=BlackboardMiscPlugin,
    )
    settings_key = "blackboard"
