from dataclasses import dataclass

from lms.product.plugin.course_copy import CourseCopyPlugin
from lms.product.plugin.grading import GradingPlugin
from lms.product.plugin.grouping import GroupingPlugin
from lms.product.plugin.misc import MiscPlugin


@dataclass
class PluginConfig:
    """A collection of plugin class definitions."""

    # These also provide the default implementations
    grading: type = GradingPlugin
    grouping: type = GroupingPlugin
    course_copy: type = CourseCopyPlugin
    misc: type = MiscPlugin


class Plugins:
    """A collection of plugins used to separate LMS specific functionality."""

    class _LazyPlugin:
        # Lazy load plugins based on the plugin config from pyramid services
        plugin_name = None

        def __set_name__(self, owner, name):
            self.plugin_name = name

        def __get__(self, instance, owner):
            plugin_class = getattr(instance._plugin_config, self.plugin_name)
            plugin = instance._request.find_service(iface=plugin_class)
            setattr(instance, self.plugin_name, plugin)  # Overwrite the attr
            return plugin

    grouping: GroupingPlugin = _LazyPlugin()
    course_copy: CourseCopyPlugin = _LazyPlugin()
    grading: GradingPlugin = _LazyPlugin()
    misc: MiscPlugin = _LazyPlugin()

    def __init__(self, request, plugin_config: PluginConfig):
        self._request = request
        self._plugin_config = plugin_config
