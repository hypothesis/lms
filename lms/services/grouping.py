from typing import List, Optional, Union

from sqlalchemy import func
from sqlalchemy.orm import aliased

from lms.models import Course, Grouping, GroupingMembership, User
from lms.models._hashed_id import hashed_id
from lms.models.grouping import Grouping
from lms.services._upsert import upsert


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
        if type_ == Grouping.Type.COURSE:
            return hashed_id(tool_consumer_instance_guid, lms_id)

        # For the rest of types, parent is mandatory
        assert parent is not None

        if type_ == Grouping.Type.CANVAS_SECTION:
            return hashed_id(tool_consumer_instance_guid, parent.lms_id, lms_id)

        return hashed_id(
            tool_consumer_instance_guid, parent.lms_id, type_.value, lms_id
        )

    def upsert_with_parent(  # pylint: disable=too-many-arguments
        self,
        tool_consumer_instance_guid,
        lms_id,
        lms_name,
        parent: Grouping,
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
        authority_provided_id = self.generate_authority_provided_id(
            tool_consumer_instance_guid, lms_id, parent, type_
        )

        return upsert(
            self._db,
            Grouping,
            query_kwargs={
                "application_instance": self._application_instance,
                "authority_provided_id": authority_provided_id,
                # These aren't really needed for querying, only for creating a new one.
                "lms_id": lms_id,
                "parent_id": parent.id,
                "type": type_,
            },
            update_kwargs={"lms_name": lms_name, "extra": extra},
        )

    def upsert_grouping_memberships(self, user: User, groups: List[Grouping]):
        """
        Upserts group memberships.

        :param user:  User the that belongs to the groups
        :param groups: List of groups the `user` belongs to
        """
        for group in groups:
            if membership := (
                self._db.query(GroupingMembership)
                .filter_by(grouping_id=group.id, user_id=user.id)
                .one_or_none()
            ):
                membership.updated = func.now()
                continue

            group.memberships.append(GroupingMembership(grouping=group, user=user))

    def get_course_groupings_for_user(
        self,
        course: Course,
        user_id: str,
        type_: Grouping.Type,
        group_set_id: Optional[Union[str, int]] = None,
    ):
        """
        Get the groupings a user belongs to in a given course.

        :param course:  The course the users belongs to
        :param user_id: User.user_id of the user we are filtering by
        :param type_: Type of subdivision within the course
        :param group_set_id: Optionally filter by `group_set_id` stored in the Course.extra
        """
        course_grouping = aliased(Course)
        query = (
            self._db.query(Grouping)
            .join(GroupingMembership)
            .join(User)
            .join(course_grouping, Grouping.parent)
            .filter(
                User.user_id == user_id,
                course_grouping.id == course.id,
                Grouping.type == type_,
            )
        )

        if group_set_id:
            query = query.filter(
                Grouping.extra["group_set_id"].astext == str(group_set_id)
            )

        return query.all()


def factory(_context, request):
    return GroupingService(
        request.db,
        request.find_service(name="application_instance"),
    )
