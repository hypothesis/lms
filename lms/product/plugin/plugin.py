from dataclasses import dataclass

from lms.product.plugin.course_service import CourseServicePlugin
from lms.product.plugin.grouping_service import GroupingServicePlugin


@dataclass
class PluginConfig:
    """A collection of plugin class definitions."""

    # These also provide the default implementations
    grouping_service: type = GroupingServicePlugin
    course_service: type = CourseServicePlugin


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

    grouping_service: GroupingServicePlugin = _LazyPlugin()
    course_service: CourseServicePlugin = _LazyPlugin()

    def __init__(self, request, plugin_config: PluginConfig):
        self._request = request
        self._plugin_config = plugin_config
