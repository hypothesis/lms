from typing import List, Optional, Union

from sqlalchemy import func
from sqlalchemy.orm import aliased

from lms.models import Course, Grouping, GroupingMembership, User
from lms.models._hashed_id import hashed_id
from lms.services.grouping._plugin import GroupingServicePlugin
from lms.services.upsert import bulk_upsert


class GroupingService:
    def __init__(self, db, application_instance, plugin: GroupingServicePlugin):
        self._db = db
        self.application_instance = application_instance
        self.plugin = plugin

    def get_authority_provided_id(
        self, lms_id, type_: Grouping.Type, parent: Optional[Grouping] = None
    ):
        guid = self.application_instance.tool_consumer_instance_guid

        if type_ == Grouping.Type.COURSE:
            assert parent is None, "Course groupings can't have a parent"
            return hashed_id(guid, lms_id)

        assert parent is not None, "Non-course groupings must have a parent"

        if type_ == Grouping.Type.CANVAS_SECTION:
            return hashed_id(guid, parent.lms_id, lms_id)

        return hashed_id(guid, parent.lms_id, type_.value, lms_id)

    def upsert_groupings(
        self,
        grouping_dicts: List[dict],
        type_: Grouping.Type,
        parent: Optional[Grouping] = None,
    ) -> List[Grouping]:
        """
        Upsert a Grouping generating the authority_provided_id based on its parent.

        :param grouping_dicts: A list of dicts containing the grouping information
        :param parent: Parent grouping for all upserted groups
        :param type_: Type of the groupings
        """
        if not grouping_dicts:
            return []

        if parent:
            if not parent.id:
                # Make sure we have a PK for the parent before upserting
                self._db.flush()
            parent_id = parent.id
        else:
            parent_id = None

        values = [
            {
                # Things we generate
                "application_instance_id": self.application_instance.id,
                "authority_provided_id": self.get_authority_provided_id(
                    grouping["lms_id"], type_, parent
                ),
                "updated": func.now(),
                # From params
                "parent_id": parent_id,
                "type": type_,
                # Things the caller provides
                "lms_id": grouping["lms_id"],
                "lms_name": grouping["lms_name"],
                "extra": grouping.get("extra"),
                "settings": grouping.get("settings"),
            }
            for grouping in grouping_dicts
        ]

        return bulk_upsert(
            self._db,
            Grouping,
            values,
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

    def get_sections(self, user, lti_user, course, grading_student_id=None):
        if not self.plugin.sections_type:
            return None

        if lti_user.is_learner:
            groupings = self.plugin.get_sections_for_learner(self, course)

        elif grading_student_id:
            groupings = self.plugin.get_sections_for_grading(
                self, course, grading_student_id
            )

        else:
            groupings = self.plugin.get_sections_for_instructor(self, course)

        return self._to_groupings(user, groupings, course, self.plugin.sections_type)

    # pylint:disable=too-many-arguments
    def get_groups(self, user, lti_user, course, group_set_id, grading_student_id=None):
        if not self.plugin.group_type:
            return None

        if lti_user.is_learner:
            groupings = self.plugin.get_groups_for_learner(self, course, group_set_id)

        elif grading_student_id:
            groupings = self.plugin.get_groups_for_grading(
                self, course, group_set_id, grading_student_id
            )

        else:
            groupings = self.plugin.get_groups_for_instructor(
                self, course, group_set_id
            )

        return self._to_groupings(user, groupings, course, self.plugin.group_type)

    def _to_groupings(self, user, groupings, course, type_):
        if groupings and not isinstance(groupings[0], Grouping):
            groupings = [
                {
                    "lms_id": grouping["id"],
                    "lms_name": grouping["name"],
                    "extra": {
                        "group_set_id": grouping.get("group_category_id")
                        or grouping.get("groupSetId")
                    },
                    "settings": grouping.get("settings"),
                }
                for grouping in groupings
            ]
            groupings = self.upsert_groupings(groupings, parent=course, type_=type_)

        self.upsert_grouping_memberships(user, groupings)

        return groupings
