from unittest import mock

from lms.validation import ValidationError


class TestValidationError:
    def test(self):
        validation_error = ValidationError(mock.sentinel.messages)

        assert validation_error.messages == mock.sentinel.messages
        assert validation_error.status_code == 422
