from dataclasses import dataclass

from lms.content_source import DEFAULT_CONTENT_SOURCES
from lms.product.d2l._d2l_files.content_source import D2LFiles
from lms.product.d2l._plugin.course_copy import D2LCourseCopyPlugin
from lms.product.d2l._plugin.grouping import D2LGroupingPlugin
from lms.product.d2l._plugin.misc import D2LMiscPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class D2L(Product):
    """A product for D2L specific settings and tweaks."""

    family: Product.Family = Product.Family.D2L

    plugin_config: PluginConfig = PluginConfig(
        grouping=D2LGroupingPlugin,
        misc=D2LMiscPlugin,
        course_copy=D2LCourseCopyPlugin,
        content_sources=tuple(list(DEFAULT_CONTENT_SOURCES) + [D2LFiles]),
    )

    route: Routes = Routes(
        oauth2_authorize="d2l_api.oauth.authorize",
        oauth2_refresh="d2l_api.oauth.refresh",
    )

    settings_key = "desire2learn"
