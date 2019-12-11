from marshmallow import Schema, fields

from lms.tool_consumer.moodle.model import Course, CourseModule
from lms.tool_consumer.moodle.module.api_module import APISubModule


class GetContentsOptions(Schema):
    excludemodules = fields.Bool(data_key="exclude_modules", default=False)
    excludecontents = fields.Bool(data_key="exclude_contents", default=False)
    includestealthmodules = fields.Bool(
        data_key="include_stealth_modules", default=True
    )
    sectionid = fields.Int(data_key="section_id")
    sectionnumber = fields.Int(data_key="section_number")
    cmid = fields.Int(data_key="course_module_id")
    modname = fields.Str(data_key="module_name")
    modid = fields.Str(data_key="module_id")


class CoreCourse(APISubModule):
    area = "core_course"

    def get_contents(
        self, course_id, **kwargs,
    ):
        """
        Get course content (modules + web service file urls)

        :param exclude_modules: Do not return modules, return only the sections structure
        :param exclude_contents: Do not return module contents (i.e: files inside a resource)
        :param include_stealth_modules: Return stealth modules for students in a special section (with id -1)
        :param section_id: Return only this section
        :param section_number: Return only this section with number (order)
        :param course_module_id: Return only this module information (among the whole sections structure)
        :param module_name: Return only modules with this name "label, forum, etc..."
        :param module_id: Return only the module with this id (to be used with modname
        """

        course_id = int(course_id)

        sections = self.call(
            "get_contents",
            params={
                "courseid": course_id,
                "options": self.ws.params.extract_dict(GetContentsOptions, kwargs),
            },
        )

        return Course.from_sections(course_id, sections)

    def get_courses(self, ids=None):
        """Return course details"""

        params = {}
        if ids:
            params["ids"] = list(int(i) for i in ids)

        return [Course(course) for course in self.call("get_courses", params)]

    def get_course_module(self, course_module_id):
        """Return information about a course module."""

        result = self.call("get_course_module", params={"cmid": int(course_module_id)})

        return CourseModule(result["cm"])

    def get_course_module_by_instance(self, module_activity_type, instance_id):
        result = self.call(
            "get_course_module_by_instance",
            params={"module": str(module_activity_type), "instance": int(instance_id)},
        )

        return CourseModule(result["cm"])
