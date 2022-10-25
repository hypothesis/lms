"""Core models of the product."""

from dataclasses import InitVar, dataclass
from enum import Enum
from typing import Dict, Optional

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
class Settings:
    groups_enabled: bool = False

    product_settings: InitVar[Dict] = field(default_factory=dict)

    def __post_init__(self, product_settings):
        self.groups_enabled = product_settings.get("groups_enabled", False)


@dataclass
class Product:
    """The main product object which is passed around the app."""

    plugin: Plugins
    settings: Settings
    plugin_config: PluginConfig = PluginConfig()
    route: Routes = Routes()
    family: Family = Family.UNKNOWN
    settings_key: Optional[str] = None
    """Key in the ai.settings dictionary that holds the product specific settings"""

    # Accessor for external consumption
    Family = Family

    @classmethod
    def from_request(cls, request):
        """Create a populated product object from the provided request."""
        ai = request.find_service(name="application_instance").get_current()
        product_settings = ai.settings.get(cls.settings_key, {})

        return cls(
            plugin=Plugins(request, cls.plugin_config),
            settings=Settings(product_settings=product_settings),
        )
