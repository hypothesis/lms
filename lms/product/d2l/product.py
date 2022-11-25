from dataclasses import dataclass

from lms.product.d2l._plugin.grouping import D2LGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class D2L(Product):
    """A product for D2L specific settings and tweaks."""

    family: Product.Family = Product.Family.D2L

    plugin_config: PluginConfig = PluginConfig(grouping=D2LGroupingPlugin)

    route: Routes = Routes(
        oauth2_authorize="d2l_api.oauth.authorize",
        oauth2_refresh="d2l_api.oauth.refresh",
        list_group_sets="d2l_api.courses.group_sets.list",
    )

    settings_key = "desire2learn"
