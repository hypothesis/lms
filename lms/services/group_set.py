from typing import TypedDict

from lms.models.group_set import LMSGroupSet
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


def factory(_context, request):
    return GroupSetService(db=request.db)
