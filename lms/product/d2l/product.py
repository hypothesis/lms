from dataclasses import dataclass

from lms.product.product import PluginConfig, Product, Routes
from lms.product.d2l._plugin.grouping import D2LGroupingPlugin


@dataclass
class D2L(Product):
    """A product for D2L specific settings and tweaks."""

    family: Product.Family = Product.Family.D2L

    route: Routes = Routes(
        oauth2_authorize="d2l_api.oauth.authorize",
        oauth2_refresh="d2l_api.oauth.refresh",
    )

    plugin_config: PluginConfig = PluginConfig(grouping_service=D2LGroupingPlugin)
