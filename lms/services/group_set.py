from typing import TypedDict

from sqlalchemy import Text, column, func, select, union

from lms.models import Course, LMSCourse, LMSCourseApplicationInstance, LMSGroupSet
from lms.services.upsert import bulk_upsert


class GroupSetDict(TypedDict):
    """Group sets are a collection of student groups."""

    id: str
    name: str


class GroupSetService:
    def __init__(self, db):
        self._db = db

    def store_group_sets(self, course: Course, group_sets: list[dict]):
        """
        Store a course's available group sets.

        We keep record of these for bookkeeping and as the basics to
        dealt with groups while doing course copy.
        """
        # Different LMS might return additional fields but we only interested in the ID and the name.
        # We explicitly cast ID to string to homogenise the data in all LMS's.
        group_sets = [{"id": str(g["id"]), "name": g["name"]} for g in group_sets]
        course.extra["group_sets"] = group_sets

        bulk_upsert(
            self._db,
            model_class=LMSGroupSet,
            values=[
                {
                    "lms_id": g["id"],
                    "name": g["name"],
                    "lms_course_id": course.lms_course.id,
                }
                for g in group_sets
            ],
            index_elements=["lms_course_id", "lms_id"],
            update_columns=["name", "updated"],
        )

    def find_group_set(
        self, application_instance, lms_id=None, name=None, context_id=None
    ) -> LMSGroupSet | None:
        """Find the first matching group set with the passed filters."""

        query = (
            select(LMSGroupSet)
            .join(LMSCourse)
            .join(LMSCourseApplicationInstance)
            .where(
                LMSCourseApplicationInstance.application_instance_id
                == application_instance.id
            )
        )
        if context_id:
            query = query.where(LMSCourse.lti_context_id == context_id)

        if lms_id:
            query = query.where(LMSGroupSet.lms_id == str(lms_id))

        if name:
            query = query.where(
                func.lower(func.trim(LMSGroupSet.name)) == func.lower(func.trim(name))
            )

        return self._db.scalars(query).first()


def factory(_context, request):
    return GroupSetService(db=request.db)
