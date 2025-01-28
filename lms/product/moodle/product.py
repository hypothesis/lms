from dataclasses import dataclass

from lms.product.moodle._plugin.course_copy import MoodleCourseCopyPlugin
from lms.product.moodle._plugin.grouping import MoodleGroupingPlugin
from lms.product.moodle._plugin.misc import MoodleMiscPlugin
from lms.product.product import Family, PluginConfig, Product, Routes


@dataclass
class Moodle(Product):
    family: Family = Family.MOODLE

    plugin_config: PluginConfig = PluginConfig(  # noqa: RUF009
        grouping=MoodleGroupingPlugin,
        course_copy=MoodleCourseCopyPlugin,
        misc=MoodleMiscPlugin,
    )

    route: Routes = Routes()  # noqa: RUF009

    settings_key = "moodle"
