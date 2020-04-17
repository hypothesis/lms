from typing import NamedTuple


class HGroup(NamedTuple):
    name: str
    authority_provided_id: str

    def groupid(self, authority):
        return f"group:{self.authority_provided_id}@{authority}"
