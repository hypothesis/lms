from lms.product.canvas._plugin.course_service import CanvasCoursePlugin
from lms.product.canvas._plugin.grouping import CanvasGroupingPlugin
from lms.product.canvas._plugin.lti_launch import CanvasLTILaunchPlugin
from lms.product.canvas.product import Canvas


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service_factory(
        CanvasGroupingPlugin.factory, iface=CanvasGroupingPlugin
    )
    config.register_service_factory(
        CanvasCoursePlugin.factory, iface=CanvasCoursePlugin
    )
    config.register_service_factory(
        CanvasLTILaunchPlugin(), iface=CanvasLTILaunchPlugin
    )
