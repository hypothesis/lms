from dataclasses import dataclass

from lms.product.moodle._plugin.course_copy import MoodleCourseCopyPlugin
from lms.product.moodle._plugin.grouping import MoodleGroupingPlugin
from lms.product.product import PluginConfig, Product, Routes


@dataclass
class Moodle(Product):
    family: Product.Family = Product.Family.MOODLE

    plugin_config: PluginConfig = PluginConfig(
        grouping=MoodleGroupingPlugin, course_copy=MoodleCourseCopyPlugin
    )

    route: Routes = Routes()

    settings_key = "moodle"
