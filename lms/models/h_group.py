from typing import NamedTuple

from lms.models._hashed_id import hashed_id

MAX_GROUP_NAME_LENGTH = 25


class HGroup(NamedTuple):
    name: str
    authority_provided_id: str
    type: str

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"

    @classmethod
    def course_group(cls, course_name, tool_consumer_instance_guid, context_id):
        """
        Create an HGroup for a course.

        :param course_name: The name of the course
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id
        """
        return HGroup(
            cls._name(course_name),
            hashed_id(tool_consumer_instance_guid, context_id),
            type="course_group",
        )

    @classmethod
    def section_group(
        cls, section_name, tool_consumer_instance_guid, context_id, section_id
    ):
        """
        Create an HGroup for a course section.

        :param section_name: The name of the section
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id the section is a part of
        :param section_id: A section id for a section group
        """
        return HGroup(
            cls._name(section_name),
            hashed_id(tool_consumer_instance_guid, context_id, section_id),
            type="section_group",
        )

    @classmethod
    def _name(cls, name):
        """Return an h-compatible group name from the given string."""

        if name is None:
            return None

        name = name.strip()

        if len(name) > MAX_GROUP_NAME_LENGTH:
            return name[: MAX_GROUP_NAME_LENGTH - 1].rstrip() + "…"

        return name
