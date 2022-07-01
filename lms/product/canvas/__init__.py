from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.canvas.product import Canvas


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service_factory(
        CanvasGroupingPlugin.factory, iface=CanvasGroupingPlugin
    )
