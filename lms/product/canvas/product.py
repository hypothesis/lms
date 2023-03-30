from dataclasses import dataclass

from lms.content_source import DEFAULT_CONTENT_SOURCES
from lms.product.canvas._canvas_files.content_source import CanvasFiles
from lms.product.canvas._plugin.course_copy import CanvasCourseCopyPlugin
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
        grouping=CanvasGroupingPlugin,
        course_copy=CanvasCourseCopyPlugin,
        content_sources=tuple(list(DEFAULT_CONTENT_SOURCES) + [CanvasFiles]),
    )

    settings_key = "canvas"
