class MoodleException(Exception):
    code = None

    def __init__(self, message, error_code):
        self.message = message
        self.error_code = error_code

        super().__init__(error_code, message)

    @classmethod
    def from_dict(cls, data):
        error_code = data.get("errorcode")
        error_class = cls

        print(data)

        for error in cls.__subclasses__():
            if error.code == error_code:
                error_class = error

        return error_class(data.get("message"), error_code)


class InvalidAPIToken(MoodleException):
    code = "invalidtoken"


class InvalidParameter(MoodleException):
    code = "invalidparameter"


class AccessControlException(MoodleException):
    code = "accessexception"
