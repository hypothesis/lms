from dataclasses import dataclass
from enum import Enum

from lms.services.grouping.plugin import GroupingServicePlugin


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


@dataclass
class Plugins:
    grouping_service: GroupingServicePlugin


@dataclass
class Product:
    plugin: Plugins
    family: Family = Family.UNKNOWN

    # Accessor for external consumption
    Family = Family

    @classmethod
    def from_request(cls, request):
        """Create a populated product object from the provided request."""
        raise NotImplementedError()
