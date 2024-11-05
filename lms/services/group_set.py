from typing import TypedDict

from sqlalchemy import Text, column, func, select, union

from lms.models import Course, Grouping, LMSGroupSet
from lms.services.upsert import bulk_upsert


class GroupSetDict(TypedDict):
    """
    Group sets are a collection of student groups.

    We store them in Course.extra
    """

    id: str
    name: str


class GroupSetService:
    def __init__(self, db):
        self._db = db

    def store_group_sets(self, course, group_sets: list[dict]):
        """
        Store this course's available group sets.

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
        self, application_instance, group_set_id=None, name=None, context_id=None
    ) -> GroupSetDict | None:
        """
        Find the first matching group set in this course.

        Group sets are stored as part of Course.extra, this method allows to query and filter them.

        :param context_id: Match only group sets of courses with this ID
        :param name: Filter courses by name
        :param group_set_id: Filter courses by ID
        """
        group_set = (
            func.jsonb_to_recordset(Course.extra["group_sets"])
            .table_valued(
                column("id", Text), column("name", Text), joins_implicitly=True
            )
            .render_derived(with_types=True)
        )

        query = self._db.query(Grouping.id, group_set.c.id, group_set.c.name).filter(
            Grouping.application_instance == application_instance
        )

        if context_id:
            query = query.filter(Grouping.lms_id == context_id)

        if group_set_id:
            query = query.filter(group_set.c.id == group_set_id)

        if name:
            query = query.filter(
                func.lower(func.trim(group_set.c.name)) == func.lower(func.trim(name))
            )

        if group_set := query.first():
            return {"id": group_set.id, "name": group_set.name}

        return None


def factory(_context, request):
    return GroupSetService(db=request.db)
