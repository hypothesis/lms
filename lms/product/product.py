from dataclasses import dataclass
from enum import Enum


@dataclass
class Product:
    class Family(str, Enum):
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

    family: Family = Family.UNKNOWN

    @classmethod
    def from_request(cls, request):
        """Create a populated product object from the provided request."""
        return cls()
