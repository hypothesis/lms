from lms.tool_consumer.moodle.model.base_model import IdentifiedModel
from lms.tool_consumer.moodle.model.course_module import CourseModule


class Course(IdentifiedModel):
    @classmethod
    def from_sections(cls, id, sections):
        return Course({"id": id, "_sections": sections})

    @property
    def sections(self):
        sections = self.get("_sections")
        if sections:
            return [CourseSection(section) for section in sections]


class CourseSection(IdentifiedModel):
    @property
    def modules(self):
        return [CourseModule(module) for module in self["modules"]]
