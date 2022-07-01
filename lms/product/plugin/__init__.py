from lms.product.plugin.grouping_service import GroupingServicePlugin
from lms.product.plugin.plugin import PluginConfig, Plugins


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service(GroupingServicePlugin(), iface=GroupingServicePlugin)
