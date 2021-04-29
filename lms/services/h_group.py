from lms.models import HGroup
from lms.models._hashed_id import hashed_id


class HGroupService:
    def __init__(self, db):
        self._db = db

    def upsert(self, name: str, authority_provided_id: str, group_type: str) -> HGroup:

        if not name:
            raise ValueError("Name is mandatory to create a group")

        h_group = (
            self._db.query(HGroup)
            .filter_by(authority_provided_id=authority_provided_id)
            .one_or_none()
        )
        if not h_group:
            h_group = HGroup(
                authority_provided_id=authority_provided_id, _name=name, type=group_type
            )
            self._db.add(h_group)
        else:
            # Update any fields that might have changed
            h_group._name = name  # pylint: disable=protected-access
            h_group.type = group_type

        return h_group

    def course_group(
        self, course_name, tool_consumer_instance_guid, context_id
    ) -> HGroup:
        """
        Get / update / create an HGroup for a course.

        :param course_name: The name of the course
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id
        """
        return self.upsert(
            course_name,
            hashed_id(tool_consumer_instance_guid, context_id),
            "course_group",
        )

    def section_group(
        self, section_name, tool_consumer_instance_guid, context_id, section_id
    ) -> HGroup:
        """
        Get / update / create an HGroup for a course section.

        :param section_name: The name of the section
        :param tool_consumer_instance_guid: Tool consumer GUID
        :param context_id: Course id the section is a part of
        :param section_id: A section id for a section group
        """
        return self.upsert(
            section_name,
            hashed_id(tool_consumer_instance_guid, context_id, section_id),
            "section_group",
        )


def factory(_context, request):
    return HGroupService(request.db)
