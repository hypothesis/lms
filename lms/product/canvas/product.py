from dataclasses import dataclass

from lms.product.canvas._plugin.course_copy import CanvasCourseCopyPlugin
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.canvas._plugin.misc import CanvasMiscPlugin
from lms.product.product import Family, PluginConfig, Product, Routes


@dataclass
class Canvas(Product):
    """A product for Canvas specific settings and tweaks."""

    family: Family = Family.CANVAS

    route: Routes = Routes(  # noqa: RUF009
        oauth2_authorize="canvas_api.oauth.authorize",
        oauth2_refresh="canvas_api.oauth.refresh",
    )

    plugin_config: PluginConfig = PluginConfig(  # noqa: RUF009
        grouping=CanvasGroupingPlugin,
        course_copy=CanvasCourseCopyPlugin,
        misc=CanvasMiscPlugin,
    )

    settings_key = "canvas"

    use_toolbar_grading = False
    """We use SpeedGrader in canvas instead"""
    use_toolbar_editing = False
    """Canvas allows re-deeplinking assignments. We don't support editing in our side."""
