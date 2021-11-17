from typing import Optional

from lms.models._hashed_id import hashed_id
from lms.models.grouping import Grouping
from lms.services.course import CourseService


class GroupingService:
    def __init__(self, db, application_instance_service):
        self._db = db
        self._application_instance = application_instance_service.get_current()

    @staticmethod
    def generate_authority_provided_id(
        tool_consumer_instance_guid,
        lms_id,
        parent: Optional[Grouping],
        type_: Grouping.Type,
    ):
        if type_ == Grouping.Type.CANVAS_SECTION:
            return hashed_id(tool_consumer_instance_guid, parent.lms_id, lms_id)
        if type_ == Grouping.Type.COURSE:
            return CourseService.generate_authority_provided_id(
                tool_consumer_instance_guid, lms_id
            )

        return hashed_id(
            tool_consumer_instance_guid,
            parent.lms_id if parent else None,
            type_,
            lms_id,
        )

    def upsert_with_parent(  # pylint: disable=too-many-arguments
        self,
        tool_consumer_instance_guid,
        lms_id,
        lms_name,
        parent: Optional[Grouping],
        type_: Grouping.Type,
        extra=None,
    ):
        """
        Upsert a Grouping generating the authority_provided_id based on its parent.

        :param tool_consumer_instance_guid: Tool consumer GUID
        :param lms_id: ID of this grouping on the LMS
        :param lms_name: Name of the grouping on the LMS
        :param parent: Parent of grouping
        :param type_: Type of the grouping
        :param extra: Any extra information to store linked to this grouping
        """
        return self._upsert(
            Grouping(
                application_instance=self._application_instance,
                authority_provided_id=self.generate_authority_provided_id(
                    tool_consumer_instance_guid, lms_id, parent, type_
                ),
                lms_id=lms_id,
                lms_name=lms_name,
                parent_id=parent.id if parent else None,
                extra=extra,
                type=type_,
            )
        )

    def _upsert(self, grouping):
        db_grouping = (
            self._db.query(Grouping)
            .filter_by(
                application_instance=grouping.application_instance,
                authority_provided_id=grouping.authority_provided_id,
            )
            .one_or_none()
        )
        if not db_grouping:
            self._db.add(grouping)
        else:
            # Update any fields that might have changed
            db_grouping.lms_name = grouping.lms_name
            db_grouping.extra = grouping.extra

        return db_grouping or grouping


def factory(_context, request):
    return GroupingService(
        request.db,
        request.find_service(name="application_instance"),
    )
