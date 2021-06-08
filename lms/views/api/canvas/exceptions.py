class CanvasGroupError(Exception):
    def __init__(self, group_set):
        self.details = {"group_set": group_set}
        super().__init__(self.details)


class CanvasGroupSetNotFound(CanvasGroupError):
    """A Canvas GroupSet not found on Canvas API."""

    error_code = "canvas_group_set_not_found"


class CanvasGroupSetEmpty(CanvasGroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "canvas_group_set_empty"


class CanvasStudentNotInGroup(CanvasGroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "canvas_student_not_in_group"
