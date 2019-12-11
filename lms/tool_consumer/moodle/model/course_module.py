from logging import getLogger

from lms.tool_consumer.moodle.model.base_model import IdentifiedModel
from lms.tool_consumer.moodle.model.enums import ActivityModuleType, GradeType

LOG = getLogger(__name__)


class CourseModule(IdentifiedModel):
    @property
    def scale_id(self):
        if self.grade_type != GradeType.SCALE:
            return None

        # Yep, scale id is stored as it's negative in 'grade'
        return -self["grade"]

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
        LOG.info("IMAAMMA %s", self)
        if self.activity_module_type != ActivityModuleType.LTI:
            LOG.debug("NOT LTI")
            return None

        if "grade" not in self:
            LOG.debug("NO GRADE")
            raise ValueError("Not enough data to determine grade type...")

        if self.get("scale") is not None:
            return GradeType.SCALE

        if self["grade"] == 0:
            LOG.debug("GRADE IS 0")
            return GradeType.NONE

        return GradeType.POINT
