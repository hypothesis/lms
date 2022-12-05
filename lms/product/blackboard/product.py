from dataclasses import dataclass

from lms.product.blackboard._plugin.files import BlackboardFilesPlugin
from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class Blackboard(Product):
    """A product for Blackboard specific settings and tweaks."""

    family: Product.Family = Product.Family.BLACKBOARD

    route: Routes = Routes(
        oauth2_authorize="blackboard_api.oauth.authorize",
        oauth2_refresh="blackboard_api.oauth.refresh",
        list_group_sets="blackboard_api.courses.group_sets.list",
        list_course_files="blackboard_api.courses.files.list",
    )

    plugin_config: PluginConfig = PluginConfig(
        grouping=BlackboardGroupingPlugin,
        files=BlackboardFilesPlugin,
    )

    settings_key = "blackboard"
