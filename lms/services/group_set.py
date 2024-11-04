from typing import TypedDict


class GroupSetDict(TypedDict):
    """
    Group sets are a collection of student groups.

    We store them in Course.extra
    """

    id: str
    name: str


class GroupSetService:
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

    def get_group_sets(self, course) -> list[GroupSetDict]:
        """Get this course's available group sets."""
        return course.extra.get("group_sets", [])


def factory(_context, _request):
    return GroupSetService()
