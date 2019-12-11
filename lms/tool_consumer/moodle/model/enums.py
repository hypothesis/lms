from enum import Enum


class GradeType(Enum):
    NONE = 0
    POINT = 1
    SCALE = -1


class ActivityModuleType(Enum):
    LTI = "lti"
    OTHER = 0
