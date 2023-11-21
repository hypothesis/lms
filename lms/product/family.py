from enum import Enum


class Family(str, Enum):
    """Enum for which product this relates to."""

    BLACKBAUD = "BlackbaudK12"
    BLACKBOARD = "BlackboardLearn"
    CANVAS = "canvas"
    D2L = "desire2learn"
    MOODLE = "moodle"
    SAKAI = "sakai"
    SCHOOLOGY = "schoology"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, _value):
        return cls.UNKNOWN
