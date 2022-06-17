class GroupError(Exception):
    def __init__(self, group_set):
        self.details = {"group_set": group_set}
        super().__init__(self.details)


class BlackboardStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "blackboard_student_not_in_group"


class BlackboardGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "blackboard_group_set_empty"


class BlackboardGroupSetNotFound(GroupError):
    error_code = "blackboard_group_set_not_found"


class CanvasGroupSetNotFound(GroupError):
    """A Canvas GroupSet not found on Canvas API."""

    error_code = "canvas_group_set_not_found"


class CanvasGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "canvas_group_set_empty"


class CanvasStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "canvas_student_not_in_group"
