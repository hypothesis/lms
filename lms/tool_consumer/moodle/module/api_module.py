class APISubModule:
    area = None

    def __init__(self, ws):
        self.ws = ws

    def call(self, function, params=None):
        if self.area is None:
            raise NotImplementedError("You must add an area to the sub-class")

        return self.ws.call(self.area, function, params)
