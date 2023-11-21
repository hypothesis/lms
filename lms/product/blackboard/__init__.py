from lms.product.blackboard._plugin.course_copy import BlackboardCourseCopyPlugin
from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.blackboard.product import Blackboard


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service_factory(
        BlackboardGroupingPlugin.factory, iface=BlackboardGroupingPlugin
    )
    config.register_service_factory(
        BlackboardCourseCopyPlugin.factory, iface=BlackboardCourseCopyPlugin
    )
