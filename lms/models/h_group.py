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
    def canvas_group(
        cls, group_name, group_id, tool_consumer_instance_guid, context_id
    ):
        """
        Create an HGroup for a canvas group.

        :param group_name: The name of the group in canvas
        :param group_id: The ID of the group in canvas
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id
        """
        return HGroup(
            cls._name(group_name),
            # TODO could we start including some of this data unhashed but we'll need to change
            # does not match "^[a-zA-Z0-9._\\-+!~*()']{1,1024}$"
            hashed_id(tool_consumer_instance_guid, context_id, group_id),
            type="canvas_group",
        )

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
            raise ValueError("Name is mandatory to create a group")

        name = name.strip()

        if len(name) > MAX_GROUP_NAME_LENGTH:
            return name[: MAX_GROUP_NAME_LENGTH - 1].rstrip() + "…"

        return name
