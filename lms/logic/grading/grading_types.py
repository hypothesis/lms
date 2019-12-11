from typing import NamedTuple


class FloatGrading(NamedTuple):
    min: float = 0
    max: float = 1
    min_increment: float = 0
    type = "float"


class IntegerGrading(NamedTuple):
    min: int = 0
    max: int = 10
    step: int = 1
    type = "integer"


class EnumeratedGrading:
    def __init__(self, value_labels):
        self.value_labels = value_labels

    def _asdict(self):
        return {
            "type": "enumerated",
            "enum": [
                {"value": value, "label": label}
                for value, label in self.value_labels.items()
            ],
        }
