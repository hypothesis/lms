from enum import Enum


class GroupError(Exception):
    class ErrorCodes(str, Enum):
        """Error codes that the FE is going to check for."""

        CANVAS_STUDENT_NOT_IN_GROUP = "canvas_student_not_in_group"
        CANVAS_GROUP_SET_EMPTY = "canvas_group_set_empty"
        CANVAS_GROUP_SET_NOT_FOUND = "canvas_group_set_not_found"
        BLACKBOARD_GROUP_SET_NOT_FOUND = "blackboard_group_set_not_found"
        BLACKBOARD_GROUP_SET_EMPTY = "blackboard_group_set_empty"
        BLACKBOARD_STUDENT_NOT_IN_GROUP = "blackboard_student_not_in_group"

    def __init__(self, error_code, group_set):
        self.error_code = error_code
        self.details = {"group_set": group_set}
        super().__init__(self.details)
