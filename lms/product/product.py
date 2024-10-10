"""Core models of the product."""

from dataclasses import InitVar, dataclass

from lms.product.family import Family
from lms.product.plugin import PluginConfig, Plugins  # type: ignore


@dataclass(frozen=True)
class Routes:
    """A collection of Pyramid route names for various functions."""

    oauth2_authorize: str | None = None
    """Authorizing with OAuth 2."""

    oauth2_refresh: str | None = None
    """Refreshing OAuth 2 tokens."""


@dataclass
class Settings:
    """Product specific settings."""

    product_settings: InitVar[dict]

    groups_enabled: bool = False
    """Is the course groups feature enabled"""

    files_enabled: bool = False
    """Is this product files feature enabled"""

    custom: dict | None = None
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
    settings_key: str | None = None
    """Key in the ai.settings dictionary that holds the product specific settings"""

    use_toolbar_grading = True
    """Whether to use grading in our toolbar."""
    use_toolbar_editing = True
    """Wether to allow assignment editing in our toolbar."""

    # Accessor for external consumption
    Family = Family

    @classmethod
    def from_request(cls, request, ai_settings: dict):
        """Create a populated product object from the provided request."""
        product_settings = ai_settings.get(cls.settings_key, {})

        return cls(
            plugin=Plugins(request, cls.plugin_config),
            settings=Settings(product_settings=product_settings),
        )
