from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.canvas._plugin.lti_params import CanvasLTIParamPlugin
from lms.product.product import PluginConfig, Product


class Canvas(Product):
    """A product for Canvas specific settings and tweaks."""

    family = Product.Family.CANVAS
    plugin_config = PluginConfig(
        grouping_service=CanvasGroupingPlugin, lti_param=CanvasLTIParamPlugin
    )
