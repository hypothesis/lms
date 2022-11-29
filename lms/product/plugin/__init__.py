from lms.product.plugin.grouping import GroupingPlugin
from lms.product.plugin.launch import LaunchPlugin
from lms.product.plugin.plugin import PluginConfig, Plugins


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service(GroupingPlugin(), iface=GroupingPlugin)
    config.register_service(LaunchPlugin(), iface=LaunchPlugin)
