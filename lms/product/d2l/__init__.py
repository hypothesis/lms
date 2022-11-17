from lms.product.d2l._plugin.grouping import D2LGroupingPlugin
from lms.product.d2l.product import D2L


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""
    config.register_service_factory(D2LGroupingPlugin.factory, iface=D2LGroupingPlugin)
