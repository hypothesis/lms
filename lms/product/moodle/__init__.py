from lms.product.moodle._plugin.course_copy import MoodleCourseCopyPlugin
from lms.product.moodle._plugin.grouping import MoodleGroupingPlugin
from lms.product.moodle._plugin.misc import MoodleMiscPlugin
from lms.product.moodle.product import Moodle


def includeme(config):  # pragma: nocover
    """Register all of our plugins."""
    config.register_service_factory(
        MoodleGroupingPlugin.factory, iface=MoodleGroupingPlugin
    )
    config.register_service_factory(
        MoodleCourseCopyPlugin.factory, iface=MoodleCourseCopyPlugin
    )
    config.register_service_factory(MoodleMiscPlugin.factory, iface=MoodleMiscPlugin)
