class APIModel(dict):
    def __init__(self, api_getter, data):
        self.api_getter = api_getter

        super().__init__(data)

    @property
    def id(self):
        return self["id"]

    @property
    def api(self):
        return self.api_getter(self.id)

    @classmethod
    def wrap(cls, api_getter, items):
        return [cls(api_getter, item) for item in items]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id} {super().__repr__()}>"
