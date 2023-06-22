from lms.product.canvas._plugin.course_copy import CanvasCourseCopyPlugin
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.canvas._plugin.misc import CanvasMiscPlugin
from lms.product.canvas.product import Canvas


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service_factory(
        CanvasGroupingPlugin.factory, iface=CanvasGroupingPlugin
    )
    config.register_service_factory(
        CanvasCourseCopyPlugin.factory, iface=CanvasCourseCopyPlugin
    )
    config.register_service_factory(CanvasMiscPlugin.factory, iface=CanvasMiscPlugin)
