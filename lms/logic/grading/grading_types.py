from typing import NamedTuple


class FloatGrading(NamedTuple):
    min: float = 0
    max: float = 10

    def as_dict(self):
        data = self._asdict()
        data['type'] = 'float'

        return data


class EnumeratedGrading:
    def __init__(self, value_labels):
        self.value_labels = value_labels

    def as_dict(self):
        return {
            "type": "enumerated",
            "enum": [
                {"value": value, "label": label}
                for value, label in self.value_labels.items()
            ],
        }
