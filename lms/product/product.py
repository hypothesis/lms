"""Core models of the product."""

from dataclasses import InitVar, dataclass
from enum import Enum
from typing import Dict, Optional

from lms.product.plugin import PluginConfig, Plugins
from lms.product.family import Family


@dataclass
class Routes:
    """A collection of Pyramid route names for various functions."""

    oauth2_authorize: Optional[str] = None
    """Authorizing with OAuth 2."""

    oauth2_refresh: Optional[str] = None
    """Refreshing OAuth 2 tokens."""


@dataclass
class Settings:
    """Product specific settings."""

    product_settings: InitVar[Dict]

    groups_enabled: bool = False
    """Is the course groups feature enabled"""

    files_enabled: bool = False
    """Is this product files feature enabled"""

    custom: Optional[dict] = None
    """Other non-standard settings."""

    def __post_init__(self, product_settings):
        self.groups_enabled = product_settings.get("groups_enabled", False)
        self.files_enabled = product_settings.get("files_enabled", False)
        self.custom = product_settings


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

    use_toolbar_grading = True
    """Whether to use grading in our toolbar."""
    use_toolbar_editing = True
    """Wether to allow assignment editing in our toolbar."""

    # Accessor for external consumption
    Family = Family

    @classmethod
    def from_request(cls, request, ai_settings: Dict):
        """Create a populated product object from the provided request."""
        product_settings = ai_settings.get(cls.settings_key, {})

        return cls(
            plugin=Plugins(request, cls.plugin_config),
            settings=Settings(product_settings=product_settings),
        )
