from collections import OrderedDict
from logging import getLogger

from lms.tool_consumer.moodle.model.base_model import IdentifiedModel

LOG = getLogger(__name__)


class ScaleValue(IdentifiedModel):
    @property
    def name(self):
        return self["name"]


class Scale(IdentifiedModel):
    @classmethod
    def from_values(cls, _id, values):
        return Scale({"id": _id, "_values": values})

    @classmethod
    def from_string(cls, _id, value_string):
        scale_values = {item.strip() for item in value_string.split(',')}

        return Scale.from_values(
            _id,
            [
                {
                    "id": pos + 1,
                    "name": value
                } for pos, value in enumerate(scale_values)
            ]
        )

    @property
    def values(self):
        values = self.get("_values")
        if not values:
            return None

        return [ScaleValue(value) for value in values]

    def values_as_dict(self):
        values = OrderedDict()
        for value in self.values:
            LOG.debug("add value %s", value)
            values[value.id] = value.name

        return values
