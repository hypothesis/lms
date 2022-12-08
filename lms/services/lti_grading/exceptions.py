from lms.services.exceptions import SerializableError


class UnknownGradingStudent(SerializableError):
    error_code = "blackboard_group_set_empty"
