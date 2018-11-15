from unittest import mock

import pytest
from requests import Response

from lms.views import HAPIError


class TestHAPIError:
    # If no ``response`` kwarg is given to HAPIError() then __str__() falls
    # back on the HTTPInternalServerError base class's __str__() which is to
    # use the given detail message string as the string representation of
    # the exception.
    def test_when_theres_no_response_uses_detail_message_as_str(self):
        err = HAPIError("Connecting to Hypothesis failed")

        assert str(err) == "Connecting to Hypothesis failed"

    # If a ``response`` arg is given to HAPIError() then it uses the
    # Response object's attributes to format a more informative string
    # representation of the exception. Not all Response objects necessarily
    # have values for every attribute - certain attributes can be ``None``
    # or the empty string, so ``__str__()`` needs to handle those.
    @pytest.mark.parametrize(
        "status_code,reason,text,expected",
        [
            (400, "Bad Request", "Name too long", "400 Bad Request Name too long"),
            (None, "Bad Request", "Name too long", "Bad Request Name too long"),
            (400, None, "Name too long", "400 Name too long"),
            (400, "Bad Request", "", "400 Bad Request"),
        ],
    )
    def test_when_theres_a_response_it_uses_it_in_str(
        self, status_code, reason, text, expected
    ):
        response = mock.create_autospec(
            Response, instance=True, status_code=status_code, reason=reason, text=text
        )
        err = HAPIError("Connecting to Hypothesis failed", response=response)

        assert str(err) == expected
