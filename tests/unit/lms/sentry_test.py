from unittest import mock

import pytest

from lms.sentry import before_send_log


class TestBeforeSendLog:
    @pytest.mark.parametrize(
        "log,should_be_filtered_out",
        [
            ({"attributes": {"logger.name": "gunicorn.access"}}, True),
            ({"attributes": {"logger.name": "foo"}}, False),
            ({}, False),
        ],
    )
    def test_it(self, log, should_be_filtered_out):
        result = before_send_log(log, mock.sentinel.hint)

        if should_be_filtered_out:
            assert result is None
        else:
            assert result == log
