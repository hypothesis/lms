from dataclasses import dataclass

from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.canvas._plugin.launch import CanvasLaunchPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class Canvas(Product):
    """A product for Canvas specific settings and tweaks."""

    family: Product.Family = Product.Family.CANVAS

    route: Routes = Routes(
        oauth2_authorize="canvas_api.oauth.authorize",
        oauth2_refresh="canvas_api.oauth.refresh",
        list_group_sets="canvas_api.courses.group_sets.list",
    )

    plugin_config: PluginConfig = PluginConfig(
        grouping=CanvasGroupingPlugin, launch=CanvasLaunchPlugin
    )

    settings_key = "canvas"

    use_grading_bar = False
    """We integrate with SpeedGrader and don't need to use the grading bar"""
