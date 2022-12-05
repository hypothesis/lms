from lms.product.blackboard._plugin.files import BlackboardFilesPlugin
from lms.product.blackboard._plugin.grouping import BlackboardGroupingPlugin
from lms.product.blackboard.product import Blackboard


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service_factory(
        BlackboardGroupingPlugin.factory, iface=BlackboardGroupingPlugin
    )
    config.register_service(BlackboardFilesPlugin(), iface=BlackboardFilesPlugin)
