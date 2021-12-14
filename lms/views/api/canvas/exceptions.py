from lms.views.api.exceptions import GroupError


class CanvasGroupSetNotFound(GroupError):
    """A Canvas GroupSet not found on Canvas API."""

    error_code = "canvas_group_set_not_found"


class CanvasGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "canvas_group_set_empty"


class CanvasStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "canvas_student_not_in_group"
