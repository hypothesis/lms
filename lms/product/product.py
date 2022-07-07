"""Core models of the product."""

from dataclasses import dataclass
from enum import Enum

from lms.product.plugin import PluginConfig, Plugins


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
class Routes:
    """A collection of Pyramid route names for various functions."""

    oauth2_authorize: str = None
    """Authorizing with OAuth 2."""

    oauth2_refresh: str = None
    """Refreshing OAuth 2 tokens."""


@dataclass
class Product:
    """The main product object which is passed around the app."""

    deep_linking = False
    """
    Does this product use deep linking to configure assignments?

    If so we will read group set info from the URL rather than the DB.
    """

    supports_grading_bar = True
    """Does this product support our built in grading bar?"""

    plugin: Plugins
    plugin_config: PluginConfig = PluginConfig()
    route: Routes = Routes()
    family: Family = Family.UNKNOWN

    # Accessor for external consumption
    Family = Family

    @classmethod
    def from_request(cls, request):
        """Create a populated product object from the provided request."""

        return cls(plugin=Plugins(request, cls.plugin_config))
