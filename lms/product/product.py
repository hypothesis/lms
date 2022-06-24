"""Core models of the product."""

from dataclasses import asdict, dataclass
from enum import Enum

from lms.models.lti_params import LTIParamPlugin
from lms.services.grouping.plugin import GroupingServicePlugin


class Family(str, Enum):
    """Enum for which product this relates to."""

    BLACKBAUD = "BlackbaudK12"
    BLACKBOARD = "BlackboardLearn"
    CANVAS = "canvas"
    D2L = "desire2learn"
    MOODLE = "moodle"
    SAKAI = "sakai"
    SCHOOLOGY = "schoology"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _value):
        return cls.UNKNOWN


@dataclass
class Plugins:
    """A collection of plugins used to separate LMS specific functionality."""

    grouping_service: GroupingServicePlugin
    lti_param: LTIParamPlugin


@dataclass
class PluginConfig:
    """A collection of plugin class definitions."""

    # These also provide the default implementations
    grouping_service: type = GroupingServicePlugin
    lti_param: type = LTIParamPlugin


@dataclass
class Product:
    """The main product object which is passed around the app."""

    plugin: Plugins
    plugin_config: PluginConfig = PluginConfig()
    family: Family = Family.UNKNOWN

    # Accessor for external consumption
    Family = Family

    @classmethod
    def from_request(cls, request):
        """Create a populated product object from the provided request."""

        plugins = {
            name: plugin_class.from_request(request)
            for name, plugin_class in asdict(cls.plugin_config).items()
        }

        return cls(plugin=Plugins(**plugins))
