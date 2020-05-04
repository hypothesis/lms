from typing import NamedTuple


class HGroup(NamedTuple):
    name: str
    authority_provided_id: str
    type: str = "course_group"

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"


def h_group_name(name):
    """Return an h-compatible group name from the given string."""
    name = name.strip()

    # The maximum length of an h group name.
    group_name_max_length = 25

    if len(name) > group_name_max_length:
        name = name[: group_name_max_length - 1].rstrip() + "…"

    return name
