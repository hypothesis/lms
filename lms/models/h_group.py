from typing import NamedTuple

from lms.models._hashed_id import hashed_id


class HGroup(NamedTuple):
    name: str
    authority_provided_id: str
    type: str = "course_group"

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"

    @classmethod
    def from_lti_parts(
        # pylint: disable=too-many-arguments
        cls,
        name,
        tool_consumer_instance_guid,
        context_id,
        section_id=None,
        type_=type,
    ):
        """
        Create an HGroup from LMS specific parts.

        :param name: The name of the course
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id
        :param section_id: A section id for a section group
        :param type_: Group type (defaults to "course_group")
        """
        return HGroup(
            name=cls._name(name) if name is not None else None,
            authority_provided_id=cls._authority_provided_id(
                tool_consumer_instance_guid, context_id, section_id
            ),
            type=type_,
        )

    @classmethod
    def _name(cls, name):
        """Return an h-compatible group name from the given string."""

        name = name.strip()

        # The maximum length of an h group name.
        group_name_max_length = 25

        if len(name) > group_name_max_length:
            name = name[: group_name_max_length - 1].rstrip() + "…"

        return name

    @classmethod
    def _authority_provided_id(
        cls, tool_consumer_instance_guid, context_id, section_id=None
    ):
        """Return an h-compatible authority_provided_id from the LTI parts."""

        if section_id is None:
            return hashed_id(tool_consumer_instance_guid, context_id)

        return hashed_id(tool_consumer_instance_guid, context_id, section_id)
