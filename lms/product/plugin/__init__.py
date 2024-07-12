# type: ignore
from lms.product.plugin.course_copy import CourseCopyPlugin
from lms.product.plugin.grouping import GroupingPlugin
from lms.product.plugin.misc import MiscPlugin
from lms.product.plugin.plugin import PluginConfig, Plugins


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""

    config.register_service(GroupingPlugin(), iface=GroupingPlugin)
    config.register_service(MiscPlugin(), iface=MiscPlugin)
    config.register_service(CourseCopyPlugin(), iface=CourseCopyPlugin)
