from pyramid import httpexceptions


class ValidationError(
    httpexceptions.HTTPUnprocessableEntity
):  # pylint: disable=too-many-ancestors
    def __init__(self, messages):
        super().__init__()
        self.messages = messages
