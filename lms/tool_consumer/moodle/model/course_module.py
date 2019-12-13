from logging import getLogger

from lms.tool_consumer.moodle.model.scale import Scale
from lms.tool_consumer.moodle.model.base_model import IdentifiedModel
from lms.tool_consumer.moodle.model.enums import ActivityModuleType, GradeType

LOG = getLogger(__name__)


class CourseModule(IdentifiedModel):
    @property
    def scale(self):
        if self.grade_type != GradeType.SCALE:
            return None

        # Yep, scale id is stored as it's negative in 'grade'
        return Scale.from_string(
            _id=-self["grade"], value_string=self['scale'])

    @property
    def max_grade(self):
        if self.grade_type != GradeType.POINT:
            return None

        return self["grade"]

    @property
    def activity_module_type(self):
        try:
            return ActivityModuleType(self["modname"])
        except ValueError:
            return ActivityModuleType.OTHER

    @property
    def is_gradable(self):
        grade_type = self.grade_type
        if not grade_type or grade_type == GradeType.NONE:
            return False

        return True

    @property
    def grade_type(self):
        if self.activity_module_type != ActivityModuleType.LTI:
            return None

        if "grade" not in self:
            raise ValueError("Not enough data to determine grade type...")

        if self.get("scale") is not None:
            return GradeType.SCALE

        if self["grade"] == 0:
            return GradeType.NONE

        return GradeType.POINT
