from dataclasses import dataclass

from lms.product.canvas._plugin.course_service import CanvasCoursePlugin
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class Canvas(Product):
    """A product for Canvas specific settings and tweaks."""

    family: Product.Family = Product.Family.CANVAS

    route: Routes = Routes(
        oauth2_authorize="canvas_api.oauth.authorize",
        oauth2_refresh="canvas_api.oauth.refresh",
    )

    plugin_config: PluginConfig = PluginConfig(
        grouping_service=CanvasGroupingPlugin, course_service=CanvasCoursePlugin
    )
