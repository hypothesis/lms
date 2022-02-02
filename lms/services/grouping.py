from typing import List, Optional, Union

from sqlalchemy import func
from sqlalchemy.orm import aliased

from lms.models import Course, Grouping, GroupingMembership, User
from lms.models._hashed_id import hashed_id
from lms.services.upsert import bulk_upsert


class GroupingService:
    def __init__(self, db, application_instance_service):
        self._db = db
        self.application_instance = application_instance_service.get_current()

    @staticmethod
    def generate_authority_provided_id(
        tool_consumer_instance_guid,
        lms_id,
        parent: Optional[Grouping],
        type_: Grouping.Type,
    ):
        if type_ == Grouping.Type.COURSE:
            assert parent is None, "Course groupings can't have a parent"
            return hashed_id(tool_consumer_instance_guid, lms_id)

        assert parent is not None, "Non-course groupings must have a parent"

        if type_ == Grouping.Type.CANVAS_SECTION:
            return hashed_id(tool_consumer_instance_guid, parent.lms_id, lms_id)

        return hashed_id(
            tool_consumer_instance_guid, parent.lms_id, type_.value, lms_id
        )

    def upsert_with_parent(
        self,
        grouping_dicts: List[dict],
        type_: Grouping.Type,
        parent: Grouping,
    ) -> List[Grouping]:
        """
        Upsert a Grouping generating the authority_provided_id based on its parent.

        :param grouping_dicts: A list of dicts containing:
            lms_id: ID of this grouping on the LMS
            lms_name: Name of the grouping on the LMS
            extra: Any extra information to store linked to this grouping

        :param parent: Parent grouping for all upserted groups
        :param type_: Type of the groupings
        """

        if not parent.id:
            # Make sure we have a PK for the parent before upserting
            self._db.flush()

        return bulk_upsert(
            self._db,
            Grouping,
            [
                {
                    "application_instance_id": self.application_instance.id,
                    "authority_provided_id": self.generate_authority_provided_id(
                        self.application_instance.tool_consumer_instance_guid,
                        grouping["lms_id"],
                        parent,
                        type_,
                    ),
                    "lms_id": grouping["lms_id"],
                    "parent_id": parent.id,
                    "type": type_,
                    "lms_name": grouping["lms_name"],
                    "extra": grouping.get("extra"),
                    "updated": func.now(),
                }
                for grouping in grouping_dicts
            ],
            index_elements=["application_instance_id", "authority_provided_id"],
            update_columns=["lms_name", "extra", "updated"],
        ).all()

    def upsert_grouping_memberships(self, user: User, groups: List[Grouping]):
        """
        Upserts group memberships.

        :param user:  User the that belongs to the groups
        :param groups: List of groups the `user` belongs to
        """
        if not user.id or any((group.id is None for group in groups)):
            # Ensure all ORM objects have their PK populated
            self._db.flush()

        bulk_upsert(
            self._db,
            GroupingMembership,
            [
                {
                    "grouping_id": group.id,
                    "user_id": user.id,
                    "updated": func.now(),
                }
                for group in groups
            ],
            index_elements=["grouping_id", "user_id"],
            update_columns=["updated"],
        )

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
