from unittest import mock

import pytest
import webargs

from lms.validation import _handle_error
from lms.validation import ValidationError


class TestHandleError:
    def test(self):
        webargs_exception = webargs.ValidationError(
            message={
                "field_name_1": ["Error message 1", "Error message 2"],
                "field_name_2": ["Error message 3"],
            }
        )

        # It wraps the webargs ValidationError in a custom ValidationError.
        with pytest.raises(ValidationError) as exc_info:
            _handle_error(
                webargs_exception,
                mock.sentinel.req,
                mock.sentinel.schema,
                mock.sentinel.status_code,
                mock.sentinel.headers,
            )

        # It exposes the webargs exception's messages as .messages.
        assert exc_info.value.messages == webargs_exception.messages

        # It raises the new exception from the original exception, so that the
        # original exception isn't lost.
        assert exc_info.value.__cause__ == webargs_exception
