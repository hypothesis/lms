class DictModel(dict):
    pass


class IdentifiedModel(DictModel):
    @property
    def id(self):
        return self["id"]

    # Allow ourselves to be used as ids in arguments to other calls
    def __int__(self):
        return self.id
