from dataclasses import dataclass

from lms.product.blackboard._plugin.course_copy import BlackboardCourseCopyPlugin
from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.blackboard._plugin.misc import BlackboardMiscPlugin
from lms.product.product import Family, PluginConfig, Product, Routes


@dataclass
class Blackboard(Product):
    """A product for Blackboard specific settings and tweaks."""

    family: Family = Family.BLACKBOARD

    route: Routes = Routes(  # noqa: RUF009
        oauth2_authorize="blackboard_api.oauth.authorize",
        oauth2_refresh="blackboard_api.oauth.refresh",
    )

    plugin_config: PluginConfig = PluginConfig(  # noqa: RUF009
        grouping=BlackboardGroupingPlugin,
        course_copy=BlackboardCourseCopyPlugin,
        misc=BlackboardMiscPlugin,
    )
    settings_key = "blackboard"
